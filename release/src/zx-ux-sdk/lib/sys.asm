; rcc runtime: process and keyboard services                (ZX-UX SDK)
SYS     equ 6003h
        section text
        global _getchar,_ticks,_yield,_sleep,_exit,_getpid,_kbdmatrix,_kbdpoll,_kbd_down
; int getchar(void): next key (raw keyboard), -1 at end of input
_getchar:
        ld a,(@israw)           ; the first time: keyboard raw, no echo
        or a
        call z,@raw
        ld hl,0
        ld de,@key
        ld bc,1
        ld a,3                  ; read
        call SYS
        j c,.e
        ld a,h
        or l
        j z,.e
        ld hl,(@key)
        ld h,0
        ret
.e:     ld hl,-1
        ret
; int kbd_down(int key): nonblocking physical Spectrum keyboard matrix.
; Returns 1 while pressed, 0 when released. ASCII letters and digits,
; SPACE and ENTER work. Uppercase letters are folded to lowercase.
; ROM GET/INKEY buffering is not involved, so held keys remain held.
_kbd_down:
        ld a,l
        cp 'A'
        jr c,.find
        cp 'Z'+1
        jr nc,.find
        or 20h
.find:  ld d,a
        ld hl,@ktab
.loop:  ld a,(hl)
        or a
        jr z,.no
        cp d
        jr z,.hit
        inc hl
        inc hl
        inc hl
        jr .loop
.hit:   inc hl
        ld b,(hl)              ; upper address byte for the row
        inc hl
        ld e,(hl)              ; individual key's active-low bit
        ld c,0FEh
        in a,(c)
        and e
        jr nz,.no
        ld hl,1
        ret
.no:    ld hl,0
        ret
; Character, port high byte, key bit.  Standard Spectrum 8x5 matrix.
@ktab:
        db 'a',0FDh,1,'b',07Fh,16,'c',0FEh,8,'d',0FDh,4
        db 'e',0FBh,4,'f',0FDh,8,'g',0FDh,16,'h',0BFh,16
        db 'i',0DFh,4,'j',0BFh,8,'k',0BFh,4,'l',0BFh,2
        db 'm',07Fh,4,'n',07Fh,8,'o',0DFh,2,'p',0DFh,1
        db 'q',0FBh,1,'r',0FBh,8,'s',0FDh,2,'t',0FBh,16
        db 'u',0DFh,8,'v',0FEh,16,'w',0FBh,2,'x',0FEh,4
        db 'y',0DFh,16,'z',0FEh,2
        db '0',0EFh,1,'1',0F7h,1,'2',0F7h,2,'3',0F7h,4
        db '4',0F7h,8,'5',0F7h,16,'6',0EFh,16,'7',0EFh,8
        db '8',0EFh,4,'9',0EFh,2,' ',07Fh,1,13,0BFh,1
        db 0
; 3DPAINT direct Q/Z/I/P/X matrix poll: 0 means no gameplay key.
; This samples the Spectrum keyboard port without blocking ZX-UX.
_kbdmatrix:
        ld bc,0FBFEh           ; Q W E R T
        in a,(c)
        bit 0,a
        jr z,.q
        ld bc,0FEFEh           ; CAPS Z X C V
        in a,(c)
        bit 1,a
        jr z,.z
        bit 2,a
        jr z,.x
        ld bc,0DFFEh           ; Y U I O P
        in a,(c)
        bit 2,a
        jr z,.i
        bit 0,a
        jr z,.p
        ld hl,0
        ret
.q:     ld hl,'q'
        ret
.z:     ld hl,'z'
        ret
.x:     ld hl,'x'
        ret
.i:     ld hl,'i'
        ret
.p:     ld hl,'p'
        ret
; The same non-blocking matrix scan also serves the game menu/editor.
_kbdpoll:
        jp _kbdmatrix
; unsigned ticks(void): 50 Hz frame counter
_ticks: ld a,38
        jp SYS
; int yield(void)
_yield: xor a
        call SYS
        ld hl,0
        ret
; int sleep(unsigned ticks)
_sleep: ld a,h
        or l
        ret z
        ld a,34
        call SYS
        ld hl,0
        ret
; int getpid(void)
_getpid:
        ld a,36
        jp SYS
; void exit(int status)
_exit:  push hl
        ld a,(@israw)
        or a
        ld a,10h                ; keyboard: cooked, echo again
        call nz,@stty
        ld hl,0
        ld a,39                 ; give the screen back
        call SYS
        pop hl
        ld h,0
        ld a,1
        call SYS
        j _exit
@raw:   ld hl,0
        ld de,@ttyb
        ld a,32                 ; gtty
        call SYS
        ld a,1
        ld (@israw),a
        ld a,20h                ; raw, no echo
        j @stty
; (apart from @raw: a program that never reads keys links only this)
@stty:  ld (@ttyb+4),a
        ld hl,0
        ld de,@ttyb
        ld a,31
        jp SYS
        section bss
@israw: ds 1
@key:   ds 2

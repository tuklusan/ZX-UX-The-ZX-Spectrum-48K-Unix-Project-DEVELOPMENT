; rcc runtime: process and keyboard services                (ZX-UX SDK)
SYS     equ 6003h
        section text
        global _getchar,_ticks,_yield,_sleep,_exit,_getpid,_kbdmatrix,_kbdpoll
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

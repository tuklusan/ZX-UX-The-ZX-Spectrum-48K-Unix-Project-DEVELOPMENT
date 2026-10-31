; ZX-UX C48 common 32x24 8x8 direct-screen glyph renderer.
; Interface: c48_cell(row, col, code), code 32..127 VGA, 128..159 game.
; Caller provides the VGA and per-game glyph tables in this module.
; Uses SDK @attr, @inv, @ovr for colors and OVER/INVERSE.
; No ROM text calls or ZX-UX UDG slots are used.
        section text
        global _c48_cell,_c48_any_key,_c48_shift_down
_c48_cell:
        ld a,l
        pop bc                  ; saved return address
        pop de                  ; column
        pop hl                  ; row
        push bc
        ld b,l                  ; row
        ld c,e                  ; column
        ld d,a                  ; glyph code
        ld a,b
        cp 24
        j nc,.done
        ld a,c
        cp 32
        j nc,.done
        ld a,d
        cp 32
        j c,.done
        cp 128
        j c,.plain
        cp 160
        j nc,.done
        sub 128                 ; 32 game glyph slots: codes 128..159
        ld hl,c48_game_glyphs
        j .idx
.plain: sub 32
        ld hl,c48_vga_font
.idx:   push hl                  ; save table base
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        pop de                  ; base of selected table
        add hl,de
        ex de,hl                ; DE = glyph scanlines
        ld a,b                  ; screen: 010TTSSS LLLCCCCC
        and 18h
        or 40h
        ld h,a
        ld a,b
        and 7
        rrca
        rrca
        rrca
        or c
        ld l,a
        push hl
        ld b,8
.draw:  ld a,(@inv)
        ld c,a
        ld a,(de)
        xor c
        ld c,a
        ld a,(@ovr)
        or a
        ld a,c
        j z,.replace
        xor (hl)
.replace:
        ld (hl),a
        inc h
        inc de
        djnz .draw
        pop hl
        ld a,h
        rrca
        rrca
        rrca
        and 3
        or 58h
        ld h,a
        ld a,(@attr)
        ld (hl),a
.done:  ld hl,0
        ret

; Physical, nonblocking 8x5 Spectrum keyboard scan.  Not the terminal
; read(0)/getchar queue: a stale gameplay keystroke must not restart a game.
_c48_any_key:
        ld bc,0FEFEh
.poll:  in a,(c)
        and 1Fh
        cp 1Fh
        jr nz,.pressed
        ld a,b
        add a,a
        or 1
        ld b,a
        cp 0FFh
        jr nz,.poll
        ld hl,0
        ret
.pressed:
        ld hl,1
        ret

; CAPS SHIFT (the physical first key of the 0xFE half-row).
_c48_shift_down:
        ld bc,0FEFEh
        in a,(c)
        and 1
        ld hl,0
        ret nz
        ld hl,1
        ret

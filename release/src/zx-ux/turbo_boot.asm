; ZX-UX beta-0.0.7 boot-only TZX receiver, independent original work.
; Never used for ordinary ZX-UX LOAD, SAVE, LDX or TAR.
; Assembled from a staged copy with generated turbo_plan.inc, turbo_lines.inc.
; Protected code D000.. below E000; scratch buffer E000..E800; SP CEFF.
;
        org 0D000h
start:  di
        ld sp,0CEFFh
        ld iy,05C3Ah
        xor a
        out (0FEh),a
        ; BASIC has just performed CLS and drawn the four ribbon cells;
        ; preserve its bitmap and attributes during all 24 progress rows.
        ld a,1
        ld (ordinal),a
        xor a
        ld (row_index),a
        ld hl,segment_plan
        ld (plan_cursor),hl
        ld hl,progress_lines
        ld (text_cursor),hl
.next:  xor a
        ld (attempts),a
        ; Before the LAST segment, draw the last progress line. The image
        ; is NOT considered complete until its own CRC/XOR/offset checks pass.
        ld a,(ordinal)
        cp 24
        jr nz,.receive
        ld hl,(text_cursor)
        call render_text_row
        ld (text_cursor),hl
.receive:
        ld a,1                   ; blue border during pilot search
        out (0FEh),a
        call receive_frame
        jr nc,.valid
        ld a,2                    ; red border on failed segment
        out (0FEh),a
        call render_error
        ld a,(attempts)
        inc a
        ld (attempts),a
        cp 4
        jr c,.receive
        ; Bound the automatic retry attempts. Operator can restart with SPACE,
        ; or cancel with BREAK (CAPS SHIFT+SPACE). Never execute partial image.
.wait_user:
        ld bc,07FFEh              ; SPACE keyboard row
        in a,(c)
        bit 0,a
        jr nz,.wait_user
        ld bc,0FEFEh              ; CAPS SHIFT row
        in a,(c)
        bit 0,a
        jp z,0000h                ; BREAK => hard reset, not partial kernel
        xor a
        ld (attempts),a
        jr .receive
.valid: ld a,0
        out (0FEh),a
        call copy_payload
        ; The 24th line must be visible while the 24th tape block is still
        ; arriving; it was drawn in .next. Earlier lines follow validation.
        ld a,(ordinal)
        cp 24
        jr z,.already_drawn
        ld hl,(text_cursor)
        call render_text_row
        ld (text_cursor),hl
.already_drawn:
        ld hl,(plan_cursor)
        ld de,4
        add hl,de
        ld (plan_cursor),hl
        ld a,(row_index)
        inc a
        ld (row_index),a
        ld a,(ordinal)
        inc a
        ld (ordinal),a
        cp 25
        jr nz,.next
        ; Every received packet has verified ordinal, offset, size, XOR and CRC.
        ld iy,05C3Ah
        ei
        ld de,250
        ld hl,407
        call 03B5h
        ld b,25
.dwell: halt
        djnz .dwell
        xor a
        out (0FEh),a             ; black border at ZX-UX handover
        ld (05C48h),a           ; BORDCR internal attribute must match black
        jp 06000h

; Read a transition from the EAR input on port FE. C bit 6 tracks phase.
; B measures delay in fixed polling-loop units; CY indicates timeout.
read_edge:
        ld b,0
.loop:  in a,(0FEh)
        xor c
        and 040h
        jr nz,.edge
        inc b
        jr z,.timeout
        jr .loop
.edge:  ld a,b
        ld (edge_width),a
        ld a,c
        xor 040h
        ld c,a
        or a                       ; CY clear
        ret
.timeout:
        scf
        ret

; Pilot has 247 long pulses. Recognize >=200 then 875/613 sync.
; Timeouts after ~2.5s do not advance the receiver's segment cursor.
find_pilot:
        ld a,0FEh
        in a,(0FEh)
        and 040h
        ld c,a
        ld e,0
        ld hl,4000                 ; >10 seconds of no tape edges
        ld (timeout_remaining),hl ; ROM CODE/boot inter-block gap can be 1.5s
.pulse: call read_edge
        jr c,.timeout
        ; Use the pilot's generous 2042 T-state pulses for authentic
        ; blue/black edge stripes. Never slow the short data-bit sampler.
        ld a,c
        and 040h
        rlca
        rlca
        out (0FEh),a
        ld a,b
        cp 28
        jr c,.short
        cp 65
        jr nc,.reset
        ld a,e
        cp 140
        jr nc,.pulse
        inc e
        ld a,(pilot_count)
        cp e
        jr nc,.pulse
        ld a,e
        ld (pilot_count),a
        jr .pulse
.short: ld a,e
        cp 140
        jr c,.reset
        ld a,b
        cp 5
        jr c,.reset
        cp 28
        jr nc,.reset
        call read_edge
        ret c
        ld a,b
        cp 4
        jr c,.reset
        cp 28
        jr nc,.reset
        or a                       ; sync accepted, carry clear
        ret
.reset: ld e,0
        jr .pulse
.timeout:
        ld e,0
        ld hl,(timeout_remaining)
        dec hl
        ld (timeout_remaining),hl
        ld a,h
        or l
        jr z,.fail
        jr .pulse
.fail:  scf
        ret

; Exactly two similar half pulses for each bit; 513/1025 T state widths.
; 8 MSB-first bits per byte, flag-free envelope (not a ROM tape header).
read_byte:
        ld d,8
        ld e,0
.bit:   sla e
        ; First transition establishes phase. Measuring it to classify a bit
        ; loses the first-byte MSB after per-byte bookkeeping on a 48K Z80.
        call read_edge
        ret c
        ld a,b
        cp 2
        jr c,.bad
        cp 35
        jr nc,.bad
        ; Classify from the *second* half-pulse, timed from a known edge.
        ; Still demand both bounded transitions; packet XOR + CRC protect
        ; against misclassification rather than running partial code.
        call read_edge
        ret c
        ld a,b
        cp 2
        jr c,.bad
        cp 35
        jr nc,.bad
        cp 15
        jr c,.zero
        set 0,e
.zero:  dec d
        jr nz,.bit
        ld a,e
        or a
        ret
.bad:   scf
        ret

receive_frame:
        ld a,'P'
        ld (stage_code),a
        call find_pilot
        ret c
        ld a,'D'
        ld (stage_code),a
        xor a
        out (0FEh),a             ; black border while decoding data
        xor a
        ld (bytes_ok),a
        ld (bytes_ok+1),a
        ld hl,(plan_cursor)
        inc hl
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld hl,11
        add hl,de
        ld (packet_bytes),hl
        ld de,(packet_bytes)
        ld hl,0E000h
.read:  push de
        call read_byte
        pop de
        ret c
        ld (hl),a
        ; Data border alternates once per VERIFIED raw byte reception;
        ; do not issue OUT inside the time-critical bit edge sampler.
        ld a,l
        and 1
        out (0FEh),a
        inc hl
        push hl
        ld hl,(bytes_ok)
        inc hl
        ld (bytes_ok),hl
        pop hl
        dec de
        ld a,d
        or e
        jr nz,.read
        ld a,'V'
        ld (stage_code),a
        call validate_frame
        ret

validate_frame:
        ld a,'H'
        ld (validation_stage),a
        ld hl,0E000h
        ld a,(hl)
        cp 'Z'
        jp nz,.bad
        inc hl
        ld a,(hl)
        cp 'X'
        jp nz,.bad
        inc hl
        ld a,(hl)
        cp 1
        jp nz,.bad
        inc hl
        ld a,(ordinal)
        cp (hl)
        jp nz,.bad
        inc hl
        ld de,(plan_cursor)
        ld a,(de)
        cp (hl)
        jp nz,.bad
        inc de
        inc hl
        ld a,(de)
        cp (hl)
        jp nz,.bad
        inc de
        inc hl
        ld a,(de)
        cp (hl)
        jp nz,.bad
        inc de
        inc hl
        ld a,(de)
        cp (hl)
        jp nz,.bad
        ld a,'X'
        ld (validation_stage),a
        ; XOR all packet bytes, including CRC and final parity.
        ld hl,0E000h
        ld de,(packet_bytes)
        ld b,0
.xor:  ld a,b
        xor (hl)
        ld b,a
        inc hl
        dec de
        ld a,d
        or e
        jr nz,.xor
        ld a,b
        or a
        jp nz,.bad
        ld a,'C'
        ld (validation_stage),a
        ; CRC-16/CCITT-FALSE over header+payload, little-endian trailer.
        ld bc,(packet_bytes)
        dec bc
        dec bc
        dec bc
        ld hl,0FFFFh
        ld de,0E000h
.crc_byte:
        push bc
        ld a,(de)
        xor h
        ld h,a
        ld b,8
.crc_bit:
        add hl,hl
        jr nc,.crc_no_xor
        ld a,h
        xor 010h
        ld h,a
        ld a,l
        xor 021h
        ld l,a
.crc_no_xor:
        djnz .crc_bit
        pop bc
        inc de
        dec bc
        ld a,b
        or c
        jr nz,.crc_byte
        ld (debug_crc),hl
        push de
        ld a,(de)
        ld (debug_crc+2),a
        inc de
        ld a,(de)
        ld (debug_crc+3),a
        pop de
        ld a,(de)
        cp l
        jp nz,.bad
        inc de
        ld a,(de)
        cp h
        jp nz,.bad
        or a
        ret
.bad:   scf
        ret

copy_payload:
        ld hl,(plan_cursor)
        ld e,(hl)
        inc hl
        ld d,(hl)                 ; offset from LOAD_BASE
        ld hl,05D98h
        add hl,de
        ex de,hl                  ; DE fixed destination
        ld hl,(plan_cursor)
        inc hl
        inc hl
        ld c,(hl)
        inc hl
        ld b,(hl)                 ; BC known segment length
        ld hl,0E008h
        ldir
        ret

render_error:
        ld a,(edge_width)
        srl a
        srl a
        srl a
        add a,'0'
        ld (error_text+2),a
        ld a,(pilot_count)
        srl a
        srl a
        srl a
        srl a
        srl a
        add a,'0'
        ld (error_text+3),a
        ; Hex byte cursor: where a packet read lost synchronization.
        ld a,(bytes_ok+1)
        call high_hex
        ld (error_text+5),a
        ld a,(bytes_ok)
        push af
        call high_hex
        ld (error_text+6),a
        pop af
        and 0fh
        call nibble_ascii
        ld (error_text+7),a
        ld a,(validation_stage)
        ld (error_text+9),a
        ld hl,0E000h
        ld de,error_text+10
        ld b,4
.print_header:
        push bc
        push hl
        ld a,(hl)
        call print_hex_byte
        pop hl
        pop bc
        inc hl
        djnz .print_header
        ld hl,debug_crc
        ld de,error_text+18
        ld b,4
.print_crc:
        push bc
        push hl
        ld a,(hl)
        call print_hex_byte
        pop hl
        pop bc
        inc hl
        djnz .print_crc
        ld a,(stage_code)
        ld (error_text),a
        ld hl,error_text
        call render_text_row
        ld a,023                 ; red paper, white ink
        jp paint_attribute

print_hex_byte:
        push af
        call high_hex
        ld (de),a
        inc de
        pop af
        and 0fh
        call nibble_ascii
        ld (de),a
        inc de
        ret

high_hex:
        rrca
        rrca
        rrca
        rrca
        and 0fh
nibble_ascii:
        add a,'0'
        cp '9'+1
        ret c
        add a,7
        ret

render_text_row:
        ; 64-column, 4x8 font from the existing ZX-UX SDK (96 glyphs).
        ; The 32 source characters each have a 4-pixel blank spacer.
        ; In row 24 keep the last 8 half-cells (4 Spectrum cells) intact.
        push hl
        pop ix
        ld a,(row_index)
        ld l,a
        ld h,0
        add hl,hl
        ld de,video_rows
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld (screen_pos),de
        ld a,(row_index)
        cp 23
        ld c,32
        jr nz,.pair
        ld c,28                  ; preserve columns 29-32 (last 4 bytes)
.pair:
        push bc
        ld a,(ix+0)
        inc ix
        call glyph_address
        push hl                  ; left glyph
        ld a,(ix+0)
        inc ix
        call glyph_address
        ex de,hl                 ; right glyph
        pop hl                   ; left glyph
        ld b,4                   ; two scanlines per packed font byte
.scan:
        ld a,(hl)
        and 0F0h
        ld c,a
        ld a,(de)
        rrca
        rrca
        rrca
        rrca
        and 00Fh
        or c
        push de
        ld de,(screen_pos)
        ld (de),a
        inc d                    ; ULA next pixel scanline
        ld (screen_pos),de
        pop de
        ld a,(hl)
        and 00Fh
        rlca
        rlca
        rlca
        rlca
        ld c,a
        ld a,(de)
        and 00Fh
        or c
        push de
        ld de,(screen_pos)
        ld (de),a
        inc d
        ld (screen_pos),de
        pop de
        inc hl
        inc de
        djnz .scan
        ld de,(screen_pos)
        ld a,d
        sub 8
        ld d,a
        inc de
        ld (screen_pos),de
        pop bc
        dec c
        jr nz,.pair
        ; Paint only columns 1..28 of the bottom row so ribbon survives.
        ld a,7
        call paint_attribute
        push ix
        pop hl
        ret

glyph_address:
        sub 32
        cp 96
        jr c,.ok
        xor a
.ok:    ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        ld bc,font4x8
        add hl,bc
        ret

paint_attribute:
        push af
        ld a,(row_index)
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,05800h
        add hl,de
        pop af
        ld b,32
        push af
        ld a,(row_index)
        cp 23
        jr nz,.attr_count
        ld b,28
.attr_count:
        pop af
.attr: ld (hl),a
        inc hl
        djnz .attr
        ret

ordinal: db 1
row_index: db 0
attempts: db 0
timeout_remaining: dw 0
packet_bytes: dw 0
bytes_ok: dw 0
stage_code: db 0
validation_stage: db 0
debug_crc: ds 4,0
edge_width: db 0
pilot_count: db 0
screen_pos: dw 0
plan_cursor: dw segment_plan
text_cursor: dw progress_lines
error_text: db '! REWIND / RETRY THIS SEGMENT  !'
video_rows:
        dup 24, n
        dw 04000h + ((n / 8) * 0800h) + ((n % 8) * 32)
        edup
segment_plan:
        include "turbo_plan.inc"
progress_lines:
        include "turbo_lines.inc"
        align 4
font4x8:
        incbin "font4x8.bin",8,384
loader_end:
        assert loader_end < 0E000h
        assert 0E000h + 11 + MAX_SEG_LEN < 0F000h
        assert loader_end < 0CEFFh || loader_end >= 0D000h

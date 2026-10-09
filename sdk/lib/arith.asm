; rcc runtime: 16-bit integer helpers                       (runix SDK)
        section text
        global @mul,@divu,@modu,@divs,@mods,@shl,@shr,@sra,@shlb,@shrb
        global @and,@or,@xor,@neg,@com,@not,@notb,@scmp,@preincw,@postincw
; HL = HL * DE
@mul:   ld b,h
        ld c,l
        ld hl,0
        ld a,16
.l:     add hl,hl
        ex de,hl
        add hl,hl
        ex de,hl
        j nc,.n
        add hl,bc
.n:     dec a
        j nz,.l
        ret
; HL = HL / DE, DE = HL % DE (unsigned); division by zero ends the program
@divu:  ld a,d
        or e
        jp z,@divz
        ld b,h
        ld c,l
        ld hl,0
        ld a,16
.l:     sla c
        rl b
        adc hl,hl
        j c,.ov
        sbc hl,de
        j nc,.s
        add hl,de
        j .n
.ov:    or a
        sbc hl,de
.s:     inc c
.n:     dec a
        j nz,.l
        ex de,hl
        ld h,b
        ld l,c
        ret
@modu:  call @divu
        ex de,hl
        ret
; signed: quotient truncates toward zero, remainder has the dividend's sign
@mods:  call @sdiv
        ex de,hl
        ret
@divs:
@sdiv:  ld a,h
        or a
        push af                 ; dividend sign
        xor d
        push af                 ; quotient sign
        bit 7,h
        call nz,@neg
        bit 7,d
        j z,.p
        ex de,hl
        call @neg
        ex de,hl
.p:     call @divu
        pop af
        call m,@neg
        pop af
        ret p
        ex de,hl
        call @neg
        ex de,hl
        ret
; shifts: HL by A (16-bit: count & 15, 8-bit: L by count & 7)
@shl:   and 15
        ret z
        ld b,a
.l:     add hl,hl
        djnz .l
        ret
@shr:   and 15
        ret z
        ld b,a
.l:     srl h
        rr l
        djnz .l
        ret
@sra:   and 15
        ret z
        ld b,a
.l:     sra h
        rr l
        djnz .l
        ret
@shlb:  and 7
        ld h,0
        ret z
        ld b,a
        ld a,l
.l:     add a,a
        djnz .l
        ld l,a
        ret
@shrb:  and 7
        ld h,0
        ret z
        ld b,a
.l:     srl l
        djnz .l
        ret
@and:   ld a,h
        and d
        ld h,a
        ld a,l
        and e
        ld l,a
        ret
@or:    ld a,h
        or d
        ld h,a
        ld a,l
        or e
        ld l,a
        ret
@xor:   ld a,h
        xor d
        ld h,a
        ld a,l
        xor e
        ld l,a
        ret
@neg:   xor a
        sub l
        ld l,a
        sbc a,a
        sub h
        ld h,a
        ret
@com:   ld a,h
        cpl
        ld h,a
        ld a,l
        cpl
        ld l,a
        ret
@not:   ld a,h
        or l
@not0:  ld hl,0
        ret nz
        inc l
        ret
@notb:  ld a,l
        or a
        j @not0
; signed compare HL with DE: CF if HL < DE, ZF if equal (HL destroyed)
@scmp:  ld a,h
        xor d
        jp m,.d
        sbc hl,de               ; CF = 0 after xor
        ret
.d:     ld a,h
        rla
        ret
; (HL) += DE; HL = new value / old value
@preincw:
        call @incw
        ex de,hl
        ret
@postincw:
        call @incw
        ld h,b
        ld l,c
        ret
@incw:  ld c,(hl)
        inc hl
        ld b,(hl)
        ex de,hl
        add hl,bc
        ex de,hl
        ld (hl),d
        dec hl
        ld (hl),e
        ret

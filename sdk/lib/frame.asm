; rcc runtime: stack frames for recursive functions        (runix SDK)
;
;   f:  call @enter / dw locals        frame: [args 1..n-1][ret][old IX] <- IX
;                                              [arg n] IX-2, locals below
;       ...  jp @leaveK   (K = n-1 pushed argument words to drop)
        section text
        global @enter,@leave,@leave0,@leave1,@leave2,@leave3
@enter: pop de
        push ix
        ld ix,0
        add ix,sp
        push hl
        ex de,hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld b,h
        ld c,l
        ld hl,0
        add hl,sp
        or a
        sbc hl,de
        push hl
        ld de,@end+170          ; keep 170 bytes for the kernel and interrupts
        or a
        sbc hl,de
        pop hl
        jp c,@noret             ; stack overflow: end the program (status 1)
        ld sp,hl
        ld h,b
        ld l,c
        jp (hl)
@leave0:
        ld sp,ix
        pop ix
        ret
@leave1:
        ld a,1
        j @leave
@leave2:
        ld a,2
        j @leave
@leave3:
        ld a,3
@leave: ld sp,ix
        pop ix
        pop de
.l:     pop bc
        dec a
        j nz,.l
        push de
        ret

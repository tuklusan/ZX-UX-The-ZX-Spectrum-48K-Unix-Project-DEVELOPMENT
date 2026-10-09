; rcc runtime: the SSB1 bytecode virtual machine            (runix SDK)
;
; A bytecode function starts   _f: call @vm / db frame / bytecode
; (rcc/bcgen.py; opcodes in rcc/bcops.py; the dispatch table @vmtab is the
; program's own, with only the instructions it uses).
; Registers: HL = top of the expression stack (the rest is on the Z80
; stack), BC = instruction pointer, IX = frame of the running function:
;   [args 1..n-1][native return][old IX] <- IX, last argument at IX-2,
;   instruction pointer saved over calls at IX-4, locals below.
; Calls and returns follow the native rcc ABI, so bytecode and native
; functions call each other.
        section text
        global @vm,@vnext
        global @v_k0,@v_k1,@v_ldk,@v_ldkw,@v_lda,@v_push,@v_pk0,@v_pk1,@v_pldk,@v_pldkw
        global @v_plda,@v_ldl,@v_ldlb,@v_stl,@v_stlb,@v_leal,@v_pldl,@v_pldlb,@v_addl,@v_addlb
        global @v_ldg,@v_ldgb,@v_stg,@v_stgb,@v_pldg,@v_pldgb,@v_addg,@v_addgb
        global @v_ldi,@v_ldib,@v_sti,@v_stib,@v_preiw,@v_postiw,@v_preib,@v_postib
        global @v_add,@v_sub,@v_mul,@v_divs,@v_divu,@v_mods,@v_modu,@v_and,@v_or,@v_xor
        global @v_shl,@v_shr,@v_sar,@v_neg,@v_com,@v_not,@v_zxb,@v_addk,@v_addkw,@v_shl1,@v_andk
        global @v_jmp,@v_jmpl,@v_jz,@v_jzl,@v_jnz,@v_jnzl,@v_jeq,@v_jeql,@v_jne,@v_jnel
        global @v_jlt,@v_jltl,@v_jge,@v_jgel,@v_jgt,@v_jgtl,@v_jle,@v_jlel
        global @v_jltu,@v_jltul,@v_jgeu,@v_jgeul,@v_jgtu,@v_jgtul,@v_jleu,@v_jleul
        global @v_jeqk,@v_jnek,@v_jltk,@v_jgek,@v_jgtk,@v_jlek,@v_adda,@v_addaw,@v_ldxb,@v_ldxw
        global @v_ldgs,@v_ldgsb,@v_stgs,@v_stgsb,@v_pldgs,@v_pldgsb,@v_addgs,@v_addgsb,@v_calli
        global @v_call,@v_ret,@v_ret0,@v_ret1,@v_ret2,@v_noret,@v_copy,@v_pop
        global @v_ldl_m2,@v_ldl_4,@v_ldl_6,@v_ldl_8,@v_ldl_m6,@v_ldl_m8,@v_ldl_m10,@v_ldl_m12
        global @v_ldl_m14,@v_ldl_m16,@v_ldl_m18,@v_ldl_m20
        global @v_stl_m2,@v_stl_4,@v_stl_6,@v_stl_m6,@v_stl_m8,@v_stl_m10,@v_stl_m12,@v_stl_m14

; enter a bytecode function (called from its native entry)
@vm:    pop bc                  ; BC -> the header
        push ix
        ld ix,0
        add ix,sp
        push hl                 ; the last argument at IX-2
        push bc                 ; (the saved IP at IX-4)
        ld a,(bc)               ; locals
        inc bc
        ld e,a
        ld d,0
        inc a
        j nz,.s
        call @vfw
.s:     ld hl,0
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
; the dispatcher: opcode -> handler, HL kept
@vnext: ld a,(bc)
        inc bc
        push hl
        ld l,a
        ld h,0
        add hl,hl
        ld de,@vmtab
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ex (sp),hl
        ret

; operands: @vfs DE = signed byte, @vfw DE = word, @vfa HL = IX + signed byte
@vfs:   ld a,(bc)
        inc bc
        ld e,a
        rla
        sbc a,a
        ld d,a
        ret
@vfw:   ld a,(bc)
        inc bc
        ld e,a
        ld a,(bc)
        inc bc
        ld d,a
        ret
@vfa:   call @vfs
        push ix
        pop hl
        add hl,de
        ret

; ---- constants and the stack
@v_pk0: push hl
@v_k0:  ld hl,0
        j @vnext
@v_pk1: push hl
@v_k1:  ld hl,1
        j @vnext
@v_pldk:
        push hl
@v_ldk: call @vfs
        ex de,hl
        j @vnext
@v_pldkw:
@v_plda:
        push hl
@v_ldkw:
@v_lda: call @vfw
        ex de,hl
        j @vnext
@v_push:
        push hl
        j @vnext
@v_pop: pop hl
        j @vnext

; ---- frame
@v_pldl:
        push hl
@v_ldl: call @vfa
@v_ldi: ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        j @vnext
@v_pldlb:
        push hl
@v_ldlb:
        call @vfa
@v_ldib:
        ld l,(hl)
        ld h,0
        j @vnext
@v_stl: push hl
        call @vfa
        pop de
@vstw:  ld (hl),e
        inc hl
        ld (hl),d
        ex de,hl
        j @vnext
@v_stlb:
        push hl
        call @vfa
        pop de
@vstb:  ld (hl),e
        ex de,hl
        j @vnext
@v_leal:
        call @vfa
        j @vnext
@v_addl:
        push hl
        call @vfa
@vaddw: push hl                 ; HL -> word, then a signed byte operand
        call @vfs
        pop hl
        ld a,(hl)
        add a,e
        ld (hl),a
        inc hl
        ld a,(hl)
        adc a,d
        ld (hl),a
        pop hl
        j @vnext
@v_addlb:
        push hl
        call @vfa
@vaddb: ld a,(bc)
        inc bc
        add a,(hl)
        ld (hl),a
        pop hl
        j @vnext

; ---- globals
@v_pldg:
        push hl
@v_ldg: call @vfw
        ex de,hl
        j @v_ldi
@v_pldgb:
        push hl
@v_ldgb:
        call @vfw
        ex de,hl
        j @v_ldib
@v_stg: call @vfw
        ex de,hl
        j @vstw
@v_stgb:
        call @vfw
        ex de,hl
        j @vstb
@v_addg:
        push hl
        call @vfw
        ex de,hl
        j @vaddw
@v_addgb:
        push hl
        call @vfw
        ex de,hl
        j @vaddb

; scalar globals: HL = @gs + the byte offset that follows
@vgs:   ld a,(bc)
        inc bc
        ld hl,@gs
        add a,l
        ld l,a
        ret nc
        inc h
        ret
@v_pldgs:
        push hl
@v_ldgs:
        call @vgs
        j @v_ldi
@v_pldgsb:
        push hl
@v_ldgsb:
        call @vgs
        j @v_ldib
@v_stgs:
        push hl
        call @vgs
        pop de
        j @vstw
@v_stgsb:
        push hl
        call @vgs
        pop de
        j @vstb
@v_addgs:
        push hl
        call @vgs
        j @vaddw
@v_addgsb:
        push hl
        call @vgs
        j @vaddb

; ---- indirect (the address on the stack, the value in HL)
@v_sti: pop de
        ex de,hl
        j @vstw
@v_stib:
        pop de
        ex de,hl
        j @vstb
; HL -> word/byte: add a signed byte to it, HL = the new / old value
@v_preiw:
        push hl
        call @vfs
        pop hl
        push hl
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        add hl,de
        ex de,hl
        pop hl
        j @vstw
@v_postiw:
        push hl
        call @vfs
        pop hl
        ld a,(hl)
        push af
        add a,e
        ld (hl),a
        inc hl
        ld a,(hl)
        push af
        adc a,d
        ld (hl),a
        pop af
        ld h,a
        pop af
        ld l,a
        j @vnext
@v_preib:
        push hl
        call @vfs
        pop hl
        ld a,(hl)
        add a,e
        ld (hl),a
        ld l,a
        ld h,0
        j @vnext
@v_postib:
        push hl
        call @vfs
        pop hl
        ld a,(hl)
        ld d,a
        add a,e
        ld (hl),a
        ld l,d
        ld h,0
        j @vnext

; ---- arithmetic (left operand on the stack)
@v_add: pop de
        add hl,de
        j @vnext
@v_sub: pop de
        ex de,hl
        or a
        sbc hl,de
        j @vnext
@v_mul: ld de,@mul
        j @vhelp
@v_divs:
        ld de,@divs
        j @vhelp
@v_divu:
        ld de,@divu
        j @vhelp
@v_mods:
        ld de,@mods
        j @vhelp
@v_modu:
        ld de,@modu
; @vhelp: HL = left (popped), DE = right, call the native helper at DE
@vhelp: ld (@vjp+1),de
        pop de
        ex de,hl
        push bc
        call @vjp
        pop bc
        j @vnext
@v_and: pop de
        ld a,l
        and e
        ld l,a
        ld a,h
        and d
        ld h,a
        j @vnext
@v_or:  pop de
        ld a,l
        or e
        ld l,a
        ld a,h
        or d
        ld h,a
        j @vnext
@v_xor: pop de
        ld a,l
        xor e
        ld l,a
        ld a,h
        xor d
        ld h,a
        j @vnext
@v_shl: ld de,@shl
        j @vsh
@v_shr: ld de,@shr
        j @vsh
@v_sar: ld de,@sra
@vsh:   ld a,l                  ; count
        ld (@vjp+1),de
        pop hl
        push bc
        call @vjp
        pop bc
        j @vnext
@v_neg: xor a
        sub l
        ld l,a
        sbc a,a
        sub h
        ld h,a
        j @vnext
@v_com: ld a,l
        cpl
        ld l,a
        ld a,h
        cpl
        ld h,a
        j @vnext
@v_not: ld a,h
        or l
        ld hl,0
        j nz,@vnext
        inc l
        j @vnext
@v_zxb: ld h,0
        j @vnext
@v_addk:
        call @vfs
        add hl,de
        j @vnext
@v_addkw:
        call @vfw
        add hl,de
        j @vnext
@v_shl1:
        add hl,hl
        j @vnext
@v_andk:
        ld a,(bc)
        inc bc
        and l
        ld l,a
        ld h,0
        j @vnext

; ---- branches: taken -> @vjs (byte offset) / @vjw (word offset), else skip
@v_jmp:
@vjs:   call @vfs
@vjump: push hl
        ld h,b
        ld l,c
        add hl,de
        ld b,h
        ld c,l
        pop hl
        j @vnext
@v_jmpl:
@vjw:   call @vfw
        j @vjump
@vno2:  inc bc
@vno1:  inc bc
        j @vnext
@v_jz:  ld a,h
        or l
        j z,@vjs
        j @vno1
@v_jzl: ld a,h
        or l
        j z,@vjw
        j @vno2
@v_jnz: ld a,h
        or l
        j nz,@vjs
        j @vno1
@v_jnzl:
        ld a,h
        or l
        j nz,@vjw
        j @vno2
@v_jeq: pop de
        or a
        sbc hl,de
        j z,@vjs
        j @vno1
@v_jeql:
        pop de
        or a
        sbc hl,de
        j z,@vjw
        j @vno2
@v_jne: pop de
        or a
        sbc hl,de
        j nz,@vjs
        j @vno1
@v_jnel:
        pop de
        or a
        sbc hl,de
        j nz,@vjw
        j @vno2
; signed: left < right
@v_jlt: call @vlt
        j c,@vjs
        j @vno1
@v_jltl:
        call @vlt
        j c,@vjw
        j @vno2
@v_jge: call @vlt
        j nc,@vjs
        j @vno1
@v_jgel:
        call @vlt
        j nc,@vjw
        j @vno2
@v_jgt: call @vgt
        j c,@vjs
        j @vno1
@v_jgtl:
        call @vgt
        j c,@vjw
        j @vno2
@v_jle: call @vgt
        j nc,@vjs
        j @vno1
@v_jlel:
        call @vgt
        j nc,@vjw
        j @vno2
; unsigned
@v_jltu:
        call @vltu
        j c,@vjs
        j @vno1
@v_jltul:
        call @vltu
        j c,@vjw
        j @vno2
@v_jgeu:
        call @vltu
        j nc,@vjs
        j @vno1
@v_jgeul:
        call @vltu
        j nc,@vjw
        j @vno2
@v_jgtu:
        call @vgtu
        j c,@vjs
        j @vno1
@v_jgtul:
        call @vgtu
        j c,@vjw
        j @vno2
@v_jleu:
        call @vgtu
        j nc,@vjs
        j @vno1
@v_jleul:
        call @vgtu
        j nc,@vjw
        j @vno2
; compare the left operand (under the return address) with HL: CF if
; left < right (@vlt, @vltu) or right < left (@vgt, @vgtu)
@vlt:   pop af
        pop de
        push af
        ex de,hl
        jp @scmp
@vgt:   pop af
        pop de
        push af
        jp @scmp
@vltu:  pop af
        pop de
        push af
        ex de,hl
        or a
        sbc hl,de
        ret
@vgtu:  pop af
        pop de
        push af
        or a
        sbc hl,de
        ret
@v_jeqk:
        call @vfs
        or a
        sbc hl,de
        j z,@vjs
        j @vno1
@v_jnek:
        call @vfs
        or a
        sbc hl,de
        j nz,@vjs
        j @vno1

; signed compare with a constant byte
@v_jltk:
        call @vfs
        call @scmp
        j c,@vjs
        j @vno1
@v_jgek:
        call @vfs
        call @scmp
        j nc,@vjs
        j @vno1
@v_jgtk:
        call @vfs               ; k < HL
        ex de,hl
        call @scmp
        j c,@vjs
        j @vno1
@v_jlek:
        call @vfs
        ex de,hl
        call @scmp
        j nc,@vjs
        j @vno1
; unsigned compare with a constant 0..127: x - lo against hi - lo (range checks)
@v_jgtuk:
        call @vfs               ; k < HL (unsigned)
        ex de,hl
        or a
        sbc hl,de
        j c,@vjs
        j @vno1
@v_jleuk:
        call @vfs
        ex de,hl
        or a
        sbc hl,de
        j nc,@vjs
        j @vno1

; ---- arrays: HL = index, the array's address follows
@v_addaw:
        add hl,hl
@v_adda:
        call @vfw
        add hl,de
        j @vnext
@v_ldxw:
        add hl,hl
        call @vfw
        add hl,de
        j @v_ldi
@v_ldxb:
        call @vfw
        add hl,de
        j @v_ldib

; ---- calls
@v_calli:                       ; through the program's call table @ct
        push hl
        ld a,(bc)
        inc bc
        ld l,a
        ld h,0
        add hl,hl
        ld de,@ct
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        pop hl
        j @vcall
@v_call:
        call @vfw               ; DE = the function
@vcall:
        ld (ix-4),c             ; (the instruction pointer)
        ld (ix-3),b
        ld bc,@vret
        push bc
        push de
        ret                     ; arguments: pushed, the last in HL
@vret:  ld c,(ix-4)
        ld b,(ix-3)
        j @vnext
@v_ret: ld a,(bc)
        j @vr
@v_ret0:
        xor a
        j @vr
@v_ret1:
        ld a,1
        j @vr
@v_ret2:
        ld a,2
@vr:    ld sp,ix                ; HL = the result
        pop ix
        pop de
.l:     or a
        j z,.d
        pop bc
        dec a
        j .l
.d:     push de
        ret
@v_noret:
        jp @noret
; copy: source on the stack, destination in HL, the count follows
@v_copy:
        call @vfw
        ld (@vt),bc
        ld b,d
        ld c,e
        ex de,hl
        pop hl
        ldir
        ld bc,(@vt)
        j @vnext

; ---- short forms
@v_pldl_m2:
        push hl
@v_ldl_m2:
        ld l,(ix-2)
        ld h,(ix-1)
        j @vnext
@v_pldl_4:
        push hl
@v_ldl_4:
        ld l,(ix+4)
        ld h,(ix+5)
        j @vnext
@v_pldl_6:
        push hl
@v_ldl_6:
        ld l,(ix+6)
        ld h,(ix+7)
        j @vnext
@v_pldl_8:
        push hl
@v_ldl_8:
        ld l,(ix+8)
        ld h,(ix+9)
        j @vnext
@v_pldl_m6:
        push hl
@v_ldl_m6:
        ld l,(ix-6)
        ld h,(ix-5)
        j @vnext
@v_pldl_m8:
        push hl
@v_ldl_m8:
        ld l,(ix-8)
        ld h,(ix-7)
        j @vnext
@v_pldl_m10:
        push hl
@v_ldl_m10:
        ld l,(ix-10)
        ld h,(ix-9)
        j @vnext
@v_pldl_m12:
        push hl
@v_ldl_m12:
        ld l,(ix-12)
        ld h,(ix-11)
        j @vnext
@v_pldl_m14:
        push hl
@v_ldl_m14:
        ld l,(ix-14)
        ld h,(ix-13)
        j @vnext
@v_pldl_m16:
        push hl
@v_ldl_m16:
        ld l,(ix-16)
        ld h,(ix-15)
        j @vnext
@v_pldl_m18:
        push hl
@v_ldl_m18:
        ld l,(ix-18)
        ld h,(ix-17)
        j @vnext
@v_pldl_m20:
        push hl
@v_ldl_m20:
        ld l,(ix-20)
        ld h,(ix-19)
        j @vnext
@v_stl_m2:
        ld (ix-2),l
        ld (ix-1),h
        j @vnext
@v_stl_4:
        ld (ix+4),l
        ld (ix+5),h
        j @vnext
@v_stl_6:
        ld (ix+6),l
        ld (ix+7),h
        j @vnext
@v_stl_m6:
        ld (ix-6),l
        ld (ix-5),h
        j @vnext
@v_stl_m8:
        ld (ix-8),l
        ld (ix-7),h
        j @vnext
@v_stl_m10:
        ld (ix-10),l
        ld (ix-9),h
        j @vnext
@v_stl_m12:
        ld (ix-12),l
        ld (ix-11),h
        j @vnext
@v_stl_m14:
        ld (ix-14),l
        ld (ix-13),h
        j @vnext
        section data
@vjp:   jp 0                    ; (self-modified: a native helper)
        section bss
@vt:    ds 2

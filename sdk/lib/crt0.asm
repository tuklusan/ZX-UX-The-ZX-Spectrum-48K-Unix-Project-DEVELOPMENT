; rcc runtime: program start-up and exit                    (runix SDK)
;
; The kernel starts a program with SP -> argc, argv[0..argc-1], 0, strings.
; @main is defined by the compiled program: it adapts main(void) or
; main(int argc, char **argv) to DE = argc, HL = argv.
SYS     equ 6003h
        section text
        global start,@noret,@divz
start:  ld hl,0
        add hl,sp
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        push hl
        push de
        call @scrinit
        pop de
        pop hl
        call @main
        jp _exit
@divz:
@noret: ld hl,1
        jp _exit

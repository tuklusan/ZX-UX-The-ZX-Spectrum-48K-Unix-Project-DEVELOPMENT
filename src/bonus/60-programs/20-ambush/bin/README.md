# 20-ambush: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC RBC_USR_MACHINE_CODE Line: 615 Statement: 4 Executable USR machine-code calls are prohibited in ZX-UX BASIC programs. ZX-UX memory check stopped line 615: USR raw_machine_code_address. 2 blocked operation(s); use --memory-policy review only for isolated tests | -RBC  615 FOR x=0 TO 7: FOR y=1 TO 9: READ a: POKE USR CHR$ (143+y)+x,a: NEXT y: NEXT x |                                                    ^
- TZX: failed (exit 1); %RBC RBC_USR_MACHINE_CODE Line: 615 Statement: 4 Executable USR machine-code calls are prohibited in ZX-UX BASIC programs. ZX-UX memory check stopped line 615: USR raw_machine_code_address. 2 blocked operation(s); use --memory-policy review only for isolated tests | -RBC  615 FOR x=0 TO 7: FOR y=1 TO 9: READ a: POKE USR CHR$ (143+y)+x,a: NEXT y: NEXT x |                                                    ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved


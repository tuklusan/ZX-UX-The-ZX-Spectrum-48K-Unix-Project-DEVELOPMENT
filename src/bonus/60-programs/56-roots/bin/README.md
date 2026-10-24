# 56-roots: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC RBC_USR_MACHINE_CODE Line: 50 Statement: 4 Executable USR machine-code calls are prohibited in ZX-UX BASIC programs. ZX-UX memory check stopped line 50: USR raw_machine_code_address. 2 blocked operation(s); use --memory-policy review only for isolated tests | -RBC   50 FOR X=1 TO 3: FOR Y=0 TO 7: READ a: POKE USR CHR$ (143+X)+Y,a: NEXT y: NEXT X |                                                    ^
- TZX: failed (exit 1); %RBC RBC_USR_MACHINE_CODE Line: 50 Statement: 4 Executable USR machine-code calls are prohibited in ZX-UX BASIC programs. ZX-UX memory check stopped line 50: USR raw_machine_code_address. 2 blocked operation(s); use --memory-policy review only for isolated tests | -RBC   50 FOR X=1 TO 3: FOR Y=0 TO 7: READ a: POKE USR CHR$ (143+X)+Y,a: NEXT y: NEXT X |                                                    ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved


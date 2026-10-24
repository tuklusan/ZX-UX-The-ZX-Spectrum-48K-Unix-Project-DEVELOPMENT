# 20-ambush: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC RBC_USR_MACHINE_CODE Line: 615 Statement: 4 Executable USR machine-code calls are prohibited in ZX-UX BASIC programs. ZX-UX memory check stopped line 615: USR raw_machine_code_address. 2 blocked operation(s); use --memory-policy review only for isolated tests | -RBC  615 FOR x=0 TO 7: FOR y=1 TO 9: READ a: POKE USR CHR$ (143+y)+x,a: NEXT y: NEXT x |                                                    ^
- TZX: failed (exit 1); %RBC RBC_USR_MACHINE_CODE Line: 615 Statement: 4 Executable USR machine-code calls are prohibited in ZX-UX BASIC programs. ZX-UX memory check stopped line 615: USR raw_machine_code_address. 2 blocked operation(s); use --memory-policy review only for isolated tests | -RBC 615 FOR {78}{3D}{30}{0E}{00}{00}{00}{00}{00}TO {37}{0E}{00}{00}{07}{00}{00}:FOR {79}{3D}{31}{0E}{00}{00}{01}{00}{00}TO {39}{0E}{00}{00}{09}{00}{00}:READ {61}:POKE USR CHR$ ({31}{34}{33}{0E}{00}{00}{8F}{00}{00}{2B}{79}){2B}{78}{2C}{61}:NEXT {79}:NEXT {78} |                                                                                                                                                                         ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved


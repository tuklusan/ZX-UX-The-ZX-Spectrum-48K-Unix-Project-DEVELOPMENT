# 52-stellar-run: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC RBC_UDG_ADDRESS Line: 8100 Statement: 5 Address of the intended user-defined graphics byte cannot be established safely. RBC E_POKE_ADDRESS: Line 8100: FOR index may receive input | -RBC 8100 FOR a=1 TO 9: READ a$: FOR b=0 TO 7: READ c: POKE USR a$+b,c: NEXT b: NEXT a |                                                        ^
- TZX: failed (exit 1); %RBC RBC_UDG_ADDRESS Line: 8100 Statement: 5 Address of the intended user-defined graphics byte cannot be established safely. RBC E_POKE_ADDRESS: Line 8100: FOR index may receive input | -RBC 8100 FOR {61}{3D}{31}{0E}{00}{00}{01}{00}{00}TO {39}{0E}{00}{00}{09}{00}{00}:READ {61}{24}:FOR {62}{3D}{30}{0E}{00}{00}{00}{00}{00}TO {37}{0E}{00}{00}{07}{00}{00}:READ {63}:POKE USR {61}{24}{2B}{62}{2C}{63}:NEXT {62}:NEXT {61} |                                                                                                                                                                                   ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved


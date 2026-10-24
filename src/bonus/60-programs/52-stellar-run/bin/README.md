# 52-stellar-run: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC RBC_UDG_ADDRESS Line: 8100 Statement: 5 Address of the intended user-defined graphics byte cannot be established safely. RBC E_POKE_ADDRESS: Line 8100: FOR index may receive input | -RBC 8100 FOR a=1 TO 9: READ a$: FOR b=0 TO 7: READ c: POKE USR a$+b,c: NEXT b: NEXT a |                                                        ^
- TZX: failed (exit 1); %RBC RBC_UDG_ADDRESS Line: 8100 Statement: 5 Address of the intended user-defined graphics byte cannot be established safely. RBC E_POKE_ADDRESS: Line 8100: FOR index may receive input | -RBC 8100 FOR a=1 TO 9: READ a$: FOR b=0 TO 7: READ c: POKE USR a$+b,c: NEXT b: NEXT a |                                                        ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved


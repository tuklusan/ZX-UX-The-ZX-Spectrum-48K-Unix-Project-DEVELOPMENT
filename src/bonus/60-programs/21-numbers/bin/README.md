# 21-numbers: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC RBC_UDG_ADDRESS Line: 555 Statement: 2 Address of the intended user-defined graphics byte cannot be established safely. RBC E_POKE_ADDRESS: Line 555: loop has no proved NEXT | -RBC  555 FOR x=0 TO 7: POKE USR "{90}"+x,32-32*INT (x/5)+(64 AND X=1): NEXT x |                         ^
- TZX: failed (exit 1); %RBC RBC_UDG_ADDRESS Line: 555 Statement: 2 Address of the intended user-defined graphics byte cannot be established safely. RBC E_POKE_ADDRESS: Line 555: loop has no proved NEXT | -RBC  555 FOR x=0 TO 7: POKE USR "{90}"+x,32-32*INT (x/5)+(64 AND X=1): NEXT x |                         ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved


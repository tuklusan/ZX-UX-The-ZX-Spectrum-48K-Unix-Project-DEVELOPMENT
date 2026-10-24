# 21-numbers: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC RBC_UDG_ADDRESS Line: 555 Statement: 2 Address of the intended user-defined graphics byte cannot be established safely. RBC E_POKE_ADDRESS: Line 555: loop has no proved NEXT | -RBC  555 FOR x=0 TO 7: POKE USR "{90}"+x,32-32*INT (x/5)+(64 AND X=1): NEXT x |                         ^
- TZX: failed (exit 1); %RBC RBC_UDG_ADDRESS Line: 555 Statement: 2 Address of the intended user-defined graphics byte cannot be established safely. RBC E_POKE_ADDRESS: Line 555: loop has no proved NEXT | -RBC 555 FOR {78}{3D}{30}{0E}{00}{00}{00}{00}{00}TO {37}{0E}{00}{00}{07}{00}{00}:POKE USR "{90}"{2B}{78}{2C}{33}{32}{0E}{00}{00}{20}{00}{00}{2D}{33}{32}{0E}{00}{00}{20}{00}{00}{2A}INT ({78}{2F}{35}{0E}{00}{00}{05}{00}{00}){2B}({36}{34}{0E}{00}{00}{40}{00}{00}AND {58}{3D}{31}{0E}{00}{00}{01}{00}{00}):NEXT {78} |                                                                                  ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved


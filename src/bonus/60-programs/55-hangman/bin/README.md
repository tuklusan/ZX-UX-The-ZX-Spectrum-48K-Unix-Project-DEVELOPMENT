# 55-hangman: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC RBC_USR_MACHINE_CODE Line: 7080 Statement: 5 Executable USR machine-code calls are prohibited in ZX-UX BASIC programs. | -RBC 7080 FOR F=1 TO 3: FOR I=1 TO 11: BEEP .02,I: NEXT I: LET I=USR 3280: NEXT F |                                                                  ^
- TZX: failed (exit 1); %RBC RBC_USR_UNRESOLVED Line: 7080 Statement: 5 USR expression cannot be proved to calculate a permitted UDG address. RBC E_USR_TOKEN: Line 7080: USR requires a proved UDG POKE address | -RBC 7080 FOR {46}{3D}{31}{0E}{00}{00}{01}{00}{00}TO {33}{0E}{00}{00}{03}{00}{00}:FOR {49}{3D}{31}{0E}{00}{00}{01}{00}{00}TO {31}{31}{0E}{00}{00}{0B}{00}{00}:BEEP {2E}{30}{32}{0E}{7B}{23}{D7}{0A}{3D}{2C}{49}:NEXT {49}:LET {49}{3D}USR {33}{32}{38}{30}{0E}{00}{00}{D0}{0C}{00}:NEXT {46} |                                                                                                                                                                                                                                       ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved


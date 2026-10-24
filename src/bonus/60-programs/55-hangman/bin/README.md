# 55-hangman: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC RBC_USR_MACHINE_CODE Line: 7080 Statement: 5 Executable USR machine-code calls are prohibited in ZX-UX BASIC programs. | -RBC 7080 FOR F=1 TO 3: FOR I=1 TO 11: BEEP .02,I: NEXT I: LET I=USR 3280: NEXT F |                                                                  ^
- TZX: failed (exit 1); %RBC RBC_USR_MACHINE_CODE Line: 7080 Statement: 5 Executable USR machine-code calls are prohibited in ZX-UX BASIC programs. | -RBC 7080 FOR F=1 TO 3: FOR I=1 TO 11: BEEP .02,I: NEXT I: LET I=USR 3280: NEXT F |                                                                  ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved


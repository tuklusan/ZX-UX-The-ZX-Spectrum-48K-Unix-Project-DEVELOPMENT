# 45-evolution-2: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC RBC_TAPE_LOAD Line: 1860 Statement: 2 LOAD requires external tape input, which standalone RBC programs do not provide. | -RBC 1860 IF INKEY$="3" THEN LOAD "" |                              ^
- TZX: failed (exit 1); %RBC RBC_TAPE_LOAD Line: 1860 Statement: 2 LOAD requires external tape input, which standalone RBC programs do not provide. | -RBC 1860 IF INKEY$="3" THEN LOAD "" |                              ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved


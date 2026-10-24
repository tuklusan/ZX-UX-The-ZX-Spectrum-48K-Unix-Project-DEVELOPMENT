# 44-evolution-1: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC RBC_TAPE_LOAD Line: 8060 Statement: 2 LOAD requires external tape input, which standalone RBC programs do not provide. | -RBC 8060 IF INKEY$="4" THEN LOAD "" |                              ^
- TZX: failed (exit 1); %RBC RBC_TAPE_LOAD Line: 8060 Statement: 2 LOAD requires external tape input, which standalone RBC programs do not provide. | -RBC 8060 IF INKEY$="4" THEN LOAD "" |                              ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved


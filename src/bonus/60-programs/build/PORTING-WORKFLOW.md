# C48 program workflow

1. Read current DEVELOPMENT main and PORTING-PROGRESS.json. Work on the
   next_program only, starting with 01-minelay after the reset. Older
   approvals/pilots count for nothing; reuse useful code rather than
   rewrite it. Original BASIC and frozen beta release remain unchanged.
2. Run original BASIC; compare the C48 game against its calculations,
   controls, edge cases, timing, visuals, state and screen remnants. Fix and
   build with python build/build-c48.py NN-name. Verify native SSX/TZX and
   actual gameplay. Run python build/check-c48.py NN-name with the required
   --system and --sdk paths; a build alone is not acceptance.
3. When final normal/adversarial/gameplay/remnants checks really pass, update
   PORTING-PROGRESS.json, then publish exactly this port and cursor together.
   Use the unchanged checker, safe fast-forward push and remote readback.
   Move to next_program only after delivery succeeds.

Keep source, necessary test code, verified executable outputs and the short
required program result. No pilot exceptions, dated reports, duplicated
screenshots, extra ledgers, handovers or ceremonial approval steps.

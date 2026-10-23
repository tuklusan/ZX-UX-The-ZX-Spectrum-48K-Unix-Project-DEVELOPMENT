# RBC FAST gate after the source-token survey — 2026-10-23

- GitHub DEVELOPMENT `main` source commit: `46ff9c300b4e006a52829b99c9b3b5ae9c751544`.
- GitHub Actions run: `40037199695`; mode: FAST, not FULL.
- Preparation passed, including the five new read-only survey unit tests.
- Compiler results: 17 of 17 inputs compiled; zero compilation failures in this FAST selection.
- Native checks ran for the FAST subset, but overall native/gameplay acceptance **failed**.
- The Galaxians fire/laser/score stage raised `AssertionError: native Galaxians fire, laser, or score regression` from `stage/fire_probe.py`. The saved `rbc-game-probe/galaxians-fire-check.json` from the failed job shows the control with 11 maximum beam pixels, zero full-laser frames and score zero; the firing run reached 134 beam pixels, 12 full-laser frames and still score zero. The laser checks passed their thresholds; the measured score-increase assertion failed. Why the shot did not raise the score remains unresolved.
- Later steps were skipped after that failure, including the native CLI check. The summarizer therefore also failed with `Expected one successful native CLI report, got 0`. This must not be counted as an independent compiler defect without further checking.
- No new numeric-USR or exact-address POKE compiler policy was installed by this commit. Therefore this FAST result does **not** revalidate the 121 original inputs under the newly accepted rules.
- Last previous FULL at source revision `1c96559ba5ff3ba423374f68e15e914d9d30838c`: 111/121 combined compile/link/native memory approvals; ten capacity failures. All those FULL results are pre-new-policy.
- Next: diagnose the actual Galaxians probe failure and preserve its values; implement the new compiler safety rules; perform FAST, BATCH and FULL again, keeping each source input's outcome separate.

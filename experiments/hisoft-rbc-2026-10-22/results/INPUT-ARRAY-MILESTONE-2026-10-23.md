# RBC numeric input-array milestone — 2026-10-23

Repository: `tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT`
Branch: `main`

## Exact source and run references

- Input string-array compiler adaptation for `51-anagrammatic`: source commit `64b854bcac788ec58682aaa55166250b0a3e9d91`, `experiments/hisoft-rbc-2026-10-22/stage/input_string_dims.py`. Native input-string capacity is 255; the narrow adaptation changes compiler input only, never archived BASIC.
- Numeric player-array adaptation for `04-horse-race` and `26-sheep-dog-trials`: source commit `f825419f4d4a63715c94e5814ca7a07132a50c17`, with a corrected token-aware matcher in source commit `1c028cf7e9d25dd7f3e289281fe23d6df9cbc65f`. Files: `experiments/hisoft-rbc-2026-10-22/stage/numeric_input_dims.py`, `experiments/hisoft-rbc-2026-10-22/tests/test_numeric_input_dims.py` and `stage/prepare_rbc.py`.
- First numeric-array full run `40017503384`, compiled 109 of 121 inputs and retained the Sheep Dog DIM failures. The exact cause was a false match on the built-in `CODE(INKEY$)` expression, not a numeric-array element. This run's failed inputs and full messages were preserved in GitHub before the correction.
- Corrected five-shard FULL run ID `40018255024`, source revision `1c028cf7e9d25dd7f3e289281fe23d6df9cbc65f`: `experiments/hisoft-rbc-2026-10-22/results/LATEST-RBC-FULL.json` (Git blob `43a8d156bf4dc75adc2d27ed9f99a5153fdab727`, saved on GitHub `main` revision `22aac760f0fc5a2a4a33f5486ce16c0af595acc4`). Preserve this historical blob if the mutable LATEST results file changes.
- The focused numeric-array test suite ran 8 tests successfully against the original `.tzx` byte sequences, with checks that modified source shapes and unbounded new accesses are rejected. The preceding string-array suite passed six focused tests. All input paths were measured by the saved five-shard run. The private text checker accepted the proposed new adapter and test files and both source commit messages.

## Full-run measured outcomes

- BASIC compilation: 111/121 inputs, comprising HELLO and 55 original BASIC text/tape pairs. Ten source failures remain, all retained with categories and full error messages in the saved structured JSON.
- Native tape startup: 50 of 55 compiled tape executables began foreground execution. Five compiled executables did not start because the frozen kernel reported `not enough memory`: `05-championship-boxing`, `13-radio-power`, `19-hobday-expenses`, `22-top-trainer`, and `41-asset-stripper`.
- `51-anagrammatic`, `04-horse-race`, and `26-sheep-dog-trials` compile from both input paths; each tape executable begins in the frozen native system and produces a nonempty bitmap. Neither startup nor a bitmap alone proves complete gameplay.
- Remaining compiler failures: `14-scuba` and `52-stellar-run` (protected shared-memory writes, four inputs); `27-picture-pairs` (unbounded memory writes, two inputs); `44-evolution-1` and `45-evolution-2` (external tape-load requests, four inputs).
- Track B remains 3/60 accepted C48 ports: regular `01-minelay` and the historical pilots `25-galaxians` and `58-invaders`. `02-fall-guy` is the next regular C48 port. The compilation count does not affect that cursor.

## Fidelity limits and open obligations

- The native numeric-array adaptation retains the original player-count variable and original player loops but reserves space for at most 128 players in Horse Race and 255 in Sheep Dog Trials. It appends a STOP guard for counts below 1 or above the native capacity. **Large input counts are not faithful equivalents to unrestricted original DIM behavior and must be recorded as a limitation, not an accepted adverse-case test.** Real gameplay, restart and numerical edge-case comparisons remain outstanding.
- The Anagrammatic input-derived DIM change uses the native compiler's 255-character INPUT width. Runtime screen states, anagram enumeration and both textual input paths still require representative comparisons with the original BASIC.
- Native startup of 50 tape executables does not close 50 complete gameplay tests. Required controls, end states, timing, actual screens and remnants are still separate proof gates.
- The 60 archived original `.bas` and `.tzx` files, frozen beta-0.2.0 release, SDK, kernel, emulator and private checker rule set were not altered to obtain these compiler results.

Next compiler work: resolve the remaining shared memory and external tape handling in the compiler and process runtime, not by rewriting archived programs or loosening the protective scanner. Address native image size in the compiler without altering frozen system files. Continue the independent C48 port queue without advancing its progress file for partial work.
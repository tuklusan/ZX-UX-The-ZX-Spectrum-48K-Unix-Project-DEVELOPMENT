# RBC original Sinclair BASIC native subset — 2026-10-23

This report records the measured 48K ZX-UX native compiler subset. The native
BASIC compiler and its tests remain development work under
`experiments/hisoft-rbc-2026-10-22/`; the frozen release and the 60 archived
BASIC text/tape pairs are unchanged.

## Verified FULL run

- GitHub Actions run: `40031609347`.
- Compiler and input source revision: `1c96559ba5ff3ba423374f68e15e914d9d30838c`.
- Canonical detail: `results/LATEST-RBC-FULL.json` on GitHub `main`.
- 121/121 input records present, no duplicate or missing entries.
- 111/121 linked, size-approved inputs passed: HELLO and both original forms
  of 55 numbered BASIC programs.
- All 55 accepted tape executables started in native ZX-UX and displayed
  nonempty graphics. A started process does not prove complete gameplay.
- 10/121 failed due to measured native memory demand over the default
  14,000-byte limit. Five affected program titles: 13-radio-power,
  19-hobday-expenses, 22-top-trainer, 27-picture-pairs, 41-asset-stripper.
  Neither BASIC input form is accepted for these five titles.
- There are zero remaining parser, protected-memory, or unsupported-RUN
  compilation failures in this final recorded run. Scuba and Evolution 1
  compile from both preserved input formats and start in native ZX-UX.
- Independent C48 port progress: three accepted of 60; next 02-fall-guy.

## Size failures (bytes of native memory required)

| Program | Original tape | Original text | Limit |
| --- | ---: | ---: | ---: |
| 13-radio-power | 18,692 | 18,695 | 14,000 |
| 19-hobday-expenses | 18,061 | 18,076 | 14,000 |
| 22-top-trainer | 20,383 | 20,383 | 14,000 |
| 27-picture-pairs | 19,511 | 19,518 | 14,000 |
| 41-asset-stripper | 18,951 | 18,951 | 14,000 |

These are explicit deployment-limit failures, not successes or untested
inputs. The errors include the measured requirement and permitted maximum.
Do not raise the limit without proof that the frozen native system can fit
and execute the resulting image.

## Default fitting and command line

The source is a Python RBC experiment, not a replacement for the frozen RCC.
RCC's current `rcc/driver.py` defaults to measured fitting for native C48.
RBC now defaults to reusing 768 printable font bytes from the real Spectrum
ROM when the source does not modify them. Scuba retains its private writable
character bank. RBC does not have RCC's BASIC bytecode backend and does not
claim to perform RCC's native/bytecode search.

- `rbc PROGRAM.bas`: linked SSX alongside the source (`PROGRAM.ssx`).
- `rbc -S PROGRAM.bas`: genuine Z80 assembly alongside the source (`PROGRAM.s`).
- `rbc -c PROGRAM.bas`: independently linkable SSO1 object alongside the
  source (`PROGRAM.sso`).
- `-o PATH`: explicitly selects the output location, as with RCC.
- `--fit` is the default; `--no-fit` retains the older embedded printable
  character font. `--max BYTES` defaults to 14,000; `--stack N` is supported.
- `--native` uses the existing backend. `--bytecode`, adjustable `--heap`,
  and arbitrary `--udgs` reservations are rejected instead of simulated.
- HELLO's default SSX, assembly, reconstructed SSO1, round-trip link, original
  source integrity and deliberate too-large result passed the native CLI gate.
  This result is recorded in the FULL JSON as `native_cli_check`.

The executable compiler is built using the checked preparation scripts and
fixed external inputs in `.github/workflows/rbc-upstream-trial.yml`; do not
claim that the experimental patches alone are a standalone compiler.

## Incomplete checks and constraints

The FULL compiler check, native starts, selected physical-key probes and
selected actual frame captures do not prove that all 55 games reach correct
end states. Complete per-title control, timing, game-state, original-screen
comparison and screen-remnant validation remains open. No results have been
relabeled to conceal this work. A green unit suite alone does not close these
requirements.

Development tests: 28 local unit tests passed for the final relocation fix.
The unchanged private checker accepted the two repaired files and commit
message on its first attempt. The final GitHub FULL result includes the
separate CLI validation. Frozen SDK, kernel, emulator, release files and all
archived BASIC files remain unmodified.

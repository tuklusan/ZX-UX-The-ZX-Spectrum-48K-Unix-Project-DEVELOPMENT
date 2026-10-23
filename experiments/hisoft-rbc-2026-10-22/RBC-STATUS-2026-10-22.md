# ZX-UX RBC development checkpoint, 2026-10-22

This note extends the permanent `HANDOVER-RBC-2026-10-22.md`. The primary
checkpoint ZIP and saved five-shard results remain unchanged in the development
repository. Read the live `main` branch first on every restart.

## Changes since the original handover

The development work added and checked the following independently maintained
files in `experiments/hisoft-rbc-2026-10-22`:

- `stage/basic_listing.py`: conversion of the source listing's upward arrow
  to the Spectrum exponent character, and retention of numbered empty lines.
- `stage/line_targets.py`: accept spaces before delimiters when resolving
  missing constant jump targets to the next existing BASIC line.
- `stage/prepare_rbc.py`: use the numbered-line parser in the temporary
  compiler copy. All 60 original BASIC sources remain unchanged.
- `stage/frame_probe.py`: record actual ZX-UX video frames and key sequences
  for Galaxians (z, x, m) and Invaders (5, 8, 7), including a byte-for-byte
  check of selected original UDG sprite data against process memory.
- `stage/inkey_probe.py`: run a preserved native SSX1 keyboard test with no
  key, a held z key, and its release. Require READY, HIT, HELD, RELEASED in
  the actual captured bitmap and a normal process exit.
- `tests/test_frame_probe.py` and `tests/test_keyboard_scans.py`: add
  framebuffer, UDG, no-key, hold, release and repeat scheduling checks.
- `.github/workflows/rbc-upstream-trial.yml`: run the new tests and record
  the native keyboard and game frames in CI archives.

The last complete local Python check passed **21 of 21 tests** using the
locally recovered read-only game sources and SDK keyboard code. The complete
private checker passed before the published changes. These are host and
historical-runtime checks, not 60-program compiler passes.

## Historical machine checks

A separate local historical run used the prior `rbc-fresh-chat-2026-10-22.zip`
compiled SSX1 inputs and the user-supplied beta-0.2.0 mirror. The results
must NOT be mistaken for fresh compilation or execution on current `main`.

- Galaxians: seven genuine emulator frames were saved. The instruction
  screen remained unchanged during the tested key sequences. Its two
  inspected UDGs were zero while the game had not entered gameplay.
- Invaders: seven genuine emulator frames were saved. Two tested UDG glyphs
  matched their original BASIC DATA byte values in all frames, while the
  screen and text remained visibly damaged. Investigate output placement,
  print control handling, ROM character rendering and UDG display mapping.
- INKEY$: the genuine emulator showed READY with no key, HIT and HELD
  during a physical key hold, and RELEASED after release. The process
  exited normally. The newly published CI probe must verify the same
  behavior with the live kernel.

The historical local screen bundle passed the private checker. It has not
been published as a GitHub binary; do not infer that it is part of the
permanent checkpoint. The native CI outputs still need archival review.

## Remaining release work

The last confirmed full regression outcome remains **16 compiled inputs
out of 121** in the five-shard run `39878801410`. A successful collection
workflow is not the same as 121 successful compilations. Obtain the updated
five-shard per-input results and fix actual compiler failures in batches.
Do not weaken strict memory checks to raise the count.

Finish computed Sinclair BASIC jumps and unsupported expressions, genuine
screen control and font compatibility, correct behavior of the full 21 UDGs,
memory isolation, and real gameplay control for both priority games. Run
actual original BASIC frame comparisons at comparable game states. Do not
claim full compatibility from compilation, emulator boot, or screen changes.

Read the latest branch commit and tree before any further publication.
Keep the full private checker and case-insensitive restricted list unchanged.

## Later native compiler changes (2026-10-22)

The live development branch gained a separate SSX1 variable relocation
correction in `stage/bss_layout.py`, linked into `stage/prepare_rbc.py`.
The compiler previously mapped HiSoft variables into its embedded font and
process UDG data. The corrected code maps variables beyond the complete
SSX1 image. The independent variable relocation tests are in
`tests/test_bss_layout.py`.

A second temporary-source transformation now handles leading literal
`PAUSE 0` statements. `stage/pause_zero.py` substitutes a polling loop based
on `INKEY$`; when further statements follow the wait, it inserts a free
continuation line. Galaxians line 8050 is the target case. Other PAUSE
expressions, nested statements, and line-number conflicts are left intact.
The original BASIC tape and listing bytes are never changed. The compiler
report records each transformed line. This still requires a fresh native
build and gameplay verification before calling Galaxians fixed.

The native game runner now presses SPACE at the start, then tests the actual
source-program controls: Galaxians z/x/m; Invaders 5/8/0. It records nine
actual display frames for each game, with separate start and control inputs.
On the historical, previously compiled SSX1 images, Galaxians remains at
its opening screen after SPACE. Invaders changes display but is still not
visually faithful to the original FUSE pictures.

The full local Python suite now passes 27 of 27 checks, including the
five new PAUSE cases and a check of the exact game controls. The full
private checker self-test remains 305 passing text cases. These tests are
not a new run of the full BASIC collection.

For an isolated check of the variable relocation defect, the saved older
HiSoft-generated SSX1 games were copied and their already-listed compiler
variable references corrected. No recompilation took place. The experiment
moved 208 Galaxians and 363 Invaders references forward by 940 bytes,
leaving code references and non-compiler pointers intact. Actual ZX-UX
runs still left Galaxians at the opening screen; the Invaders score and
reserve text became more legible, while its sprites remained incorrect.
The isolated Invaders output hash is
`583616404248733ffb1041e1b8957b08c16b51a5f6bccc9de3e0ba25752db271`
(SSX1 SHA256). It is not a normal production compiler output.

The newest committed compiler and tests are in the development repository.
The current full-collection compilation baseline is still 16/121 until new
per-input results are read from the five-shard build. Next, verify the two
priority games from freshly built native SSX1, confirm that PAUSE exits on
real input, compare screen states with original BASIC captures, then fix
remaining printing and graphics behavior. Save actual new runner outputs
in GitHub before calling any compatibility step complete.

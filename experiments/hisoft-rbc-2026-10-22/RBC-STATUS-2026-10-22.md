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

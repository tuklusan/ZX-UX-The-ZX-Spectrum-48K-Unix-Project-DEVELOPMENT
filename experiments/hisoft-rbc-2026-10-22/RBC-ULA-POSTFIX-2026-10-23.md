# RBC native ULA checkpoint — 2026-10-23

Repository: `tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT`, branch `main`.
The upstream emulator change at `b655d67e6a519d47ff2321dacba890e330a16e5c`
implements cassette EAR input and idle audio feedback for supported Issue 2 and
Issue 3 ULA models. The two emulator copies in the repository are unchanged by
this RBC cleanup.

## Removed experiment-only input override

- Delete `stage/keyboard_ula.py`, which previously wrapped CPU port reads and
  forced bit 6 high with no cassette pulses.
- `stage/frame_probe.py` and `stage/gameplay_ports.py` now read the genuine
  emulator ports without replacing, wrapping, or intercepting them.
- `tests/test_keyboard_ula.py` checks the real emulator for Issue 2, Issue 3,
  ordinary key release, audio output states, and active cassette edges. It no
  longer imports the removed test-only module.
- Prior ZIP archives and the old EAR handover are historical records only;
  they are not current source for these native tests.

## Verified native behavior

The unchanged Galaxians tape-built SSX1 image and actual ZX-UX system tape
were exercised with the corrected `dist/sdk/bin/py/zxmachine.py` matching the
upstream blob. No keyboard byte was altered or substituted. The emulator offers
an Issue 2/Issue 3 ULA hardware choice. The original Galaxians BASIC uses
full-byte keyboard-port comparisons and depends on the audio feedback level.

- **Issue 2**: after selecting the supported ULA model, SPACE begins the game,
  held Z moves the ship left, and held X moves the ship right. The direct
  movement test passed. Both Galaxians and Invaders produced nine actual native
  captures; the font stayed intact and tested sprite bytes matched original
  DATA values. Invaders retains the default Issue 3 test profile.
- **Issue 3**: with the emulator's default audio state, the same Galaxians
  movement test did not move the ship. Direct observation found bit 6 low
  during the relevant full-byte keyboard reads. This is a remaining hardware
  profile compatibility difference, not a compiler success claim.
- The local host suite passed 36 tests. The last complete five-shard CI run
  (39894329893) passed, with **16 of 121 compilation inputs** successful;
  this count has not improved from the current hardware cleanup.
- Earlier firing and 40-point scoring results used the retired test-only
  override. Repeat that comparison under the native Issue 2 profile before
  claiming firing and scoring as independently confirmed without intervention.

## Screen colors versus preserved BASIC screenshots

Side-by-side inspection of actual native gameplay frames against the untouched
original `02-MAIN.png` images found incomplete color fidelity:

- Galaxians uses the same broad screen color roles in the compared states:
  black background, cyan enemies, green enemy figures, and white text/ship.
  A frame-by-frame exact color match has not been established.
- Invaders retains its cyan background and magenta lower defenses, but the
  original black enemy glyphs and score text render light gray/white in the
  native capture. The 48/49 aligned enemy cells measure geometry only, not
  attribute or palette equivalence. The native text also appears enlarged
  in the displayed PNG because the emulator capture uses a different pixel
  scaling from the original preserved image.

A production INK/PAPER/attribute comparison remains open. Neither the ULA
input repair nor the experimental hardware profile is a color fix.

## Current verification and recovery

The added `RBC-NATIVE-ULA-POSTFIX-CAPTURES-2026-10-23.zip` preserves the unaltered
binary outputs of this run, real screenshots, reports, source SHA256 values,
and explicit Issue 2/Issue 3 results. Original BASIC sources remain untouched.
The previously saved `rbc-native-controls-checkpoint-2026-10-22.zip` contains
historic compiler and binary records, but its input override must not be used.

Use the current `main` files under `stage/` and `tests/`. Run the private
checker and all tests before each push. Repeat five-shard compilation and native
screen/gameplay tests after further compiler changes. Keep the full checker and
case-insensitive restricted text rules unchanged.

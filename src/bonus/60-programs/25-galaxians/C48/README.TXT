GALAXIANS -- experimental C48 port (number 25)

This is the C48 translation of BASIC/25-galaxians.bas, using the frozen
C48 compiler and the shared renderer in ../../c48lib/.
Original BASIC files and reference screenshots were not changed.

Controls: Z left, X right, M fire. Any key starts at the intro.
The six-ship fleet, falling attackers, scoring, explosions, and restart
screen are translated from the original BASIC game.

Source: galaxian.c is the C48 gameplay; galaxian-glyphs.asm holds the
14 original BASIC 8x8 sprites. The builder creates a temporary
galaxian.asm companion under ../../build/tmp/ by combining the shared
c48lib.asm, c48lib-font.asm and local sprite table. This generated file
is not committed and is removed on a successful build.
galaxian.ssx is the ZX-UX executable;
galaxian.tzx is a cassette with internal executable name galaxian.

Rebuild (from src/bonus/60-programs/):
  python build/build-c48.py 25-galaxians
Or pass --sdk PATH when the frozen SDK is located elsewhere.
The builder uses ../../build/tmp/ for intermediates and publishes only
SSX and TZX into this C48 directory. The shared VGA font's
source and terms are documented in ../../c48lib/FONT-SOURCE.txt.

FIX: The 3-cell-wide mothership animation used to leave white pixels
behind. The prior mothership position is now cleared before each new
position. A cleanup is also done between the two movement passes.
This is a source-level fix; the test captures did not reach the end-of-
fleet mothership sequence, so its exact appearance has not been proven.

Checks: C48 compile/link PASSED with frozen SDK. TZX generated from
SSX with frozen rtap. Actual ZX-UX kernel execution in frozen rvm:
intro and moving game state observed after booting the ZX-UX system.
SCREENSHOTS/01-C48-INTRO.png, 02-C48-GAMEPLAY.png and
03-C48-AFTER-FIRE.png are genuine captures of the rebuilt executable.
Historical references: ../BASIC/SCREENSHOTS/ and KEYS-AND-TIMING.TXT.
The historical FUSE clock times include tape loading and are not valid
for direct ZX-UX wall-clock matching. Full behavioral equivalence,
collision pixel accuracy, mothership animation, exact sound timing and
loading with yolo are not yet independently proven.

2026-10-22 source and adversarial review:
- The new shared c48_any_key checks all eight physical keyboard rows.
  The original first draft of this scan did not terminate with no key;
  emulator review caught and corrected it before publishing.
- The intro and GAME OVER prompts now wait for release, a fresh physical
  press and release. The game sets ZX-UX terminal raw/non-echo mode so
  terminal key events cannot print over the bitmap game display.
- Independent BASIC DATA review checks all 14 original sprite shapes.
- Automated real-kernel tests exercise the intro, gameplay, GAME OVER
  prompt held idle for 120 frames and a fresh game restart. The saved
  SCREENSHOTS/04-C48-GAME-OVER-WAIT.png is from the actual ZX-UX rvm run.
- Run from src/bonus/60-programs/: python build/test-c48.py --system
  PATH/ZX-UX.tzx --sdk PATH/ZX-UX-SDK [--captures]
  The system tape requires its matching kernel.json in the same directory.
- Still open: visually exercised fleet-completion mothership animation,
  exhaustive BASIC collision and score equivalence, FUSE-versus-C48
  motion and sound comparison, and running the TZX through ZX-UX yolo.
  This experimental port is NOT declared fully behaviorally verified.

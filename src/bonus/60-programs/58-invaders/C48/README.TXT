INVADERS -- experimental C48 translation (number 58)

Port of the historical BASIC/58-invaders.bas by Michael Bews.
The original BASIC files, tapes and selected FUSE screenshots are unchanged.

Controls from the BASIC: 5 left, 8 right, 7/up fire. Shifted cursor
movements can move five cells. A key begins the game at the intro.
Rules translated from BASIC: seven rows of seven aliens, advancing
formation, randomized five-glyph command ship at the top, launcher,
laser shields, 60 reserve rockets, blocked firing behind shield sectors,
20 per invader, 200 per command ship hit, -10 per miss, fleet victory,
planet defeat, highest score and running total across games.

Files:
  invaders.c            Game translation and logical screen collision grid
  invaders-glyphs.asm   13 original BASIC glyphs plus a rocket glyph
  (invaders.asm)        Generated only under ../../build/tmp/, not tracked
  invaders.ssx          Frozen SDK SSX executable
  invaders.tzx          ZX-UX cassette, internal name invaders
  SCREENSHOTS/          Actual ZX-UX kernel emulator screen captures

Shared files: ../../c48lib/c48lib.asm, c48lib-font.asm, c48lib.h,
FONT-SOURCE.txt. The font is Acer VGA 8x8, deliberately unlike the
Spectrum ROM font. The shared renderer writes directly to screen RAM
and never consumes a BASIC game UDG slot.
Build (from src/bonus/60-programs/):
  python build/build-c48.py 58-invaders
Or pass --sdk PATH for a separate frozen SDK checkout. Generated assembly
is assembled under ../../build/tmp/ and removed after successful builds.
Only the final SSX/TZX outputs are published into C48/.

BASIC references: ../BASIC/58-invaders.bas, KEYS-AND-TIMING.TXT and
SCREENSHOTS/01-INTRO.png, 02-MAIN.png, 03-AFTER-INPUT.png.
Historical captures were made at 15.968, 24.952 and 27.947 seconds
from FUSE runner launch (including tape load and RUN at 320% speed).
The ZX-UX timing is not directly comparable; compare equivalent states.

Validation: C48 source compiled and linked with frozen SDK. SSX and
TZX generated; headless frozen rvm booted the real ZX-UX system and
ran Invaders through its intro and formation scenes. Captures:
SCREENSHOTS/01-C48-INTRO.png, 02-C48-GAMEPLAY.png,
03-C48-AFTER-FIRE.png (keys were sent; firing or score change was
not demonstrated in the captured frame).

Limitations: The alternate font changes text width/appearance, and
an overprinted underscore title was removed to avoid corrupting the
headline. An optional logical character grid models BASIC SCREEN$
for rocket collision testing; full collision equivalence is unproven.
BASIC numeric formatting, command-ship randomness, arrow-key repeats,
replay timing and BEEP sound have not been independently matched.
Not all win/loss/restart branches were exercised. The yolo tape loader
has not been independently tested on a running machine.

2026-10-22 source and adversarial review:
- Intro and replay prompts now require release, a fresh physical press,
  then release, instead of consuming buffered terminal getchar input.
  Both programs enable raw/non-echo tty mode using frozen gtty/stty.
- An animated vertical rocket is drawn with extra sprite 141 rather than
  incorrectly printing ASCII 97 ('a'). A missile is visibly rendered in
  successive screen rows before impact; an alien hit was observed.
- MISS! is now transient and its HUD area is cleared; ordinary score and
  rocket reserve values are then refreshed. The moving command ship has
  separately tracked hit bounds and must match an actual ship glyph.
- CAPS SHIFT+5/8 now produces five-cell moves as with BASIC's cursor keys;
  the frozen SDK's kbd_down(8/9) does not represent shifted cursors.
- The BASIC DATA reference pass checks 13 original sprites byte for byte,
  including its interleaved POKE/READ layouts. Sprite 141 is a new rocket.
- Automated real ZX-UX kernel checks drove the launcher, observed the
  rocket in flight, verified score 20 and reserve 59 after a hit, then
  score 10 and reserve 58 after a miss, with no HUD remnants, and CAPS
  SHIFT fast movement. Actual captures were saved as
  SCREENSHOTS/04-C48-ROCKET-FLIGHT.png and 05-C48-SCORED-HIT.png.
- Run: python build/test-c48.py --system PATH/ZX-UX.tzx
  --sdk PATH/ZX-UX-SDK [--captures] (requires adjacent kernel.json).
- NOT YET VERIFIED: actual 200-point command ship strike, victory and
  defeat/restart sequences, all collision branches, sound
  equivalence to BASIC, and ZX-UX yolo loading of the cassette. This
  remains an experimental port; no full-equivalence claim is made.

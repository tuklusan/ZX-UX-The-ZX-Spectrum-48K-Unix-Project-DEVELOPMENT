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
  invaders-glyphs.asm   13 original 8x8 sprite glyphs from BASIC DATA
  invaders.asm          Generated matching companion, not hand-maintained
  invaders.ssx          Frozen SDK SSX executable
  invaders.tzx          ZX-UX cassette, internal name invaders
  SCREENSHOTS/          Actual ZX-UX kernel emulator screen captures

Shared files: ../../c48lib/c48lib.asm, c48lib-font.asm, c48lib.h,
FONT-SOURCE.txt. The font is Acer VGA 8x8, deliberately unlike the
Spectrum ROM font. The shared renderer writes directly to screen RAM
and never consumes a BASIC game UDG slot.
Build (from src/bonus/60-programs/):
  python build/build.py 58-invaders
Or pass --sdk PATH for a separate frozen SDK checkout.

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

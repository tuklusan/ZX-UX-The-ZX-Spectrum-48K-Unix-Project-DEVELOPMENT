MINELAY -- experimental C48 translation, numbered program 01.

Original input: ../BASIC/01-minelay.bas (historical bytes unchanged).
Uses the frozen C48 SDK, common c48lib Acer VGA 8x8 renderer and seven
original BASIC bitmap glyphs in minelay-glyphs.asm. No platform changes.

BASIC mapping and features:
  1-20: startup, original game introduction, score state
  50-150: player loop, Q/Z vertical and I/P horizontal movement, walls,
          gold (+10), axe pickups, lives and enemy encounters
  700-940: pursuing mine-layer, trail and occasional object spawning
  5000-6007: axe against walls, collisions, life loss, respawn
  6020-6050: game over and difficulty 1 (hard) / 2 (easier)
  7000-7850: random maze, eggs, mines, axes, player and enemy starts
  9000-9040: seven 8x8 UDG sprites, transcribed byte-for-byte
  9500-9999: introductory text and decorative animation

Built source: minelay.c. Final native outputs: minelay.ssx and minelay.tzx
with executable tape name minelay. Generated minelay.asm is temporary
and must never be checked in. To rebuild from the 60-programs root:
  python build/build-c48.py 01-minelay

Actual test performed in a disposable copy with frozen compiler/assembler:
compiled and linked SSX; packaged TZX; booted the real frozen ZX-UX
kernel with the headless RVM emulator; observed intro, choice menu,
maze/gameplay and movement via P. Score changed from 0 to 10 during the
recorded input sequence. Actual C48 snapshots in SCREENSHOTS/.
Historical FUSE reference: ../BASIC/SCREENSHOTS/. Full pixel-wise match
is not expected across independent random seeds or the alternate font.

KNOWN DIFFERENCES AND OPEN VERIFICATION:
- The BASIC animated MINELAY title is currently a static text header.
- The original uses fractional mine-layer movement, SCREEN$/ATTR reads,
  randomized maze generation and exact print semantics. The C48 model
  uses a 2x logical coordinate and a logical cell/attribute grid;
  arithmetic, collision and generated maze equivalence need further audit.
- Need exhaustive normal and adversarial checks of gold, axes, mine
  collisions, lives, high scores, difficult/easy distribution, endgame,
  restart, no leftover screen items, and exact keyboard/timing/sound.
- A full BASIC-versus-C48 visual review and actual yolo TZX loading
  have not been demonstrated. Independent three-clean-scan audit gate
  has NOT passed; this is NOT a finished or equivalent port.

Progress is committed as a source/compile/runtime checkpoint only.
The final v0.4 workflow closeout is still BLOCKED until its checks pass.

Repeatable automated checks (from this C48 folder):
  python test-minelay.py --system PATH/ZX-UX.tzx --sdk PATH/sdk/bin/py
The test confirms the 56 BASIC glyph bytes and executes the real ZX-UX
kernel through intro idle, menu, maze startup and movement. This is a
smoke test, not a substitute for three clean independent audits.

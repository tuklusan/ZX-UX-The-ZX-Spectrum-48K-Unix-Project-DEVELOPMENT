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

2026-10-22 source-fidelity correction — BASIC SCREEN$ retries:
- BASIC lines 7410 and 7520 retry random placement if the target
  SCREEN$ is empty (including all seven custom graphic cells). The
  initial C48 version placed eggs and mines over existing UDG objects.
- make_maze() now retries a random position while the logical cell is
  a custom glyph (codes 128..159), keeping walls, eggs, mines, and axes
  intact. This applies to the original 20 eggs and 10 mines; the later
  opportunistic spawn is deliberately unchanged, matching BASIC.
- Added independent source/glyph assertions to test-minelay.py.
  Rebuilt the frozen C48 SSX and TZX twice with identical SHA-256 values,
  executed the real frozen ZX-UX system in rvm, and drove intro,
  difficulty choice, maze initialization, and P movement successfully.
- SCREENSHOTS/04-C48-MAZE-RETRY-VERIFICATION.png is a real
  headless-kernel capture. It verifies active display, not full game
  equivalence or individual randomly selected target rejection.
- Still incomplete: animated BASIC opening, exact mine pursuit and
  collision timing, lives/axe/endgame paths, three consecutive full
  disk-byte audits, and yolo cassette loading. Completion gate BLOCKED.

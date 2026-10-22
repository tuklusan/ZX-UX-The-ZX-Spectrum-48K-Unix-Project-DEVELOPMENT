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

Additional adversarial runtime regression:
- With all movement keys released, the active mine-layer eventually
  depletes the three player lives and reaches the GAME OVER screen.
- The screen remained unchanged through an additional 120 idle frames;
  an explicit new 1 keypress started a fresh hard-difficulty maze.
- The per-program test now exercises this real ZX-UX kernel path, in
  addition to original UDG bytes, introduction, menu, maze and movement.
  SCREENSHOTS/05-C48-GAME-OVER-IDLE.png is a genuine frozen-RVM frame.
- Full three-round source audit, exact intro animation, axe effects,
  collision fidelity and yolo tape loading are still outstanding.

2026-10-22 pursuer-versus-laid-mine redraw correction:
- BASIC 700 clears the old mine-layer location and can leave a mine at
  the previous one. BASIC 720 then draws the pursuer at its new position.
- The C48 translation previously drew the pursuer first and deposited
  a mine last. When a 0.5-cell move keeps the same displayed position,
  that mine covered the pursuer sprite. Reordered C48 drawing to match
  the original and to prevent the temporary disappearance.
- New source-order and original-BASIC assertions in test-minelay.py,
  plus a real frozen ZX-UX kernel bitmap check that locates the exact
  8x8 mine-layer glyph in multiple subsequent gameplay frames.
- SCREENSHOTS/06-C48-PURSUER-TRAIL-ORDER.png is a genuine headless
  ZX-UX gameplay capture. Two isolated builds produced identical SSX
  and TZX bytes; the full existing intro/menu/maze/movement/game-over/
  replay smoke regression passed. Original BASIC remains unchanged.
- This is a verified incremental fix, NOT final completion: the
  opening animation, deeper collision/axe parity, yolo loading, and
  the three clean independent disk-byte review rounds remain open.

2026-10-22 BASIC title animation and ENTER prompt update:
- The static C48 MINELAY heading was replaced with the original BASIC
  line-9500 title bitmap pattern (157 characters over five 32-column
  rows). The 64 underscore cells animate into the original graphic
  code-150 shape, with red ink, white paper, sound and the small
  pixel-line highlights of BASIC line 9645.
- Shifted the original instructions below the five title rows.
  Start now waits for a fresh physical ENTER key (supported as
  kbd_down(13) in frozen C48), not just any key.
- SCREENSHOTS/07-C48-ANIMATED-TITLE.png is a genuine headless ZX-UX
  framebuffer capture from the final rebuilt program. The title
  resembles the original BASIC screenshot, but animation timing
  and the text/font rendering remain nonidentical.
- test-minelay.py checks all 157 source pattern characters, ENTER
  polling, input transitions, the mine-layer sprite, game-over and
  restart. The full real-kernel test passed after the intro timing
  and ENTER changes. Two final builds produced identical SSX/TZX
  hashes. A further combined build+runtime re-run later timed out;
  do not count that timed-out attempt as a passing check.
- Original BASIC not changed. Completion gate remains OPEN:
  exact pursuit and collision fidelity, axe, sound and timing,
  full three-consecutive-round independent audit, and yolo loading
  are not all demonstrated.

2026-10-22 collision cleanup and screen-remnant review:
- BASIC line 6000 clears the active mine-layer cell (my,mx) before
  relocating it. The C48 collision handler could relocate its logical
  coordinates without erasing the old visible glyph, leaving a ghost
  after a collision with a laid mine. It now blanks the active pursuer
  cell before respawn in both life-loss and axe-protected collision
  cases. A protected overlapping collision redraws the player once
  the mine-layer has moved.
- Added BASIC line 6000 source-fidelity assertions and a screen-level
  adversarial check sampling six genuine ZX-UX gameplay/game-over frames,
  rejecting any frame containing more than one visible pursuer glyph.
- Two builds under the frozen SDK produced byte-identical SSX/TZX.
  The real ZX-UX kernel regression passed original glyphs, placements,
  title, keyboard/maze/movement, pursuing-sprite visibility,
  game-over, idle wait, fresh restart, and the sampled ghost check.
  The private checker passed both changed text files.
- An earlier over-dense 45-snapshot emulator run timed out and is
  expressly NOT counted as passing; the six-snapshot check completed.
- This remains an experimental port: the complete BASIC-to-C48 normal
  and adversarial review, three successive clean fresh-disk-byte
  audits, axe behavior parity, full timing/sound and yolo tape
  execution remain unverified. No BASIC or frozen platform file changed.

2026-10-22 BASIC line 705 mine trail position correction:
- BASIC saves my1/mx1 before each 0.5-cell mine-layer movement and
  uses those saved pre-movement coordinates to lay a mine in its
  following iteration (line 700). C48 formerly saved the coordinates
  after movement, depositing some mines one half-step too far forward.
- mine_step now saves previous_my/previous_mx before moving and uses
  these for old_my/old_mx after drawing the current mine-layer.
  Mine drawing remains before the active pursuer, as in BASIC 720.
- Added a source regression asserting the exact BASIC 705 statement,
  the pre-move state capture, and the retained draw order.
- Frozen C48 builds passed twice with identical SSX and TZX SHA-256;
  real ZX-UX kernel regression passed glyphs, intro, difficulty,
  movement, pursuer visibility, six no-ghost frames, game over, idle
  and hard restart. Private text checker passed both changed sources.
- This is an incremental fix. The three independent clean scan rounds,
  full axe and collision parity, sound/timing and yolo loading remain
  open; do not declare the port equivalent or complete.

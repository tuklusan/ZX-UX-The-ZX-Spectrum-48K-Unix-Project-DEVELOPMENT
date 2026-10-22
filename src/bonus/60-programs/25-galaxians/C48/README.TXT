GALAXIANS -- experimental C48 translation (Spectrum 60 / program 25)

This is a new C48 version of the historical 25-galaxians BASIC game.
The original BASIC files in ../BASIC/ have not been changed.

Files:
  galaxian.c          C48 game logic and controls
  galaxian.asm        Z80 32-column 8x8 VGA text and 14 game glyphs
  galaxian.ssx        frozen C48 linker output, SSX1
  galaxian.tzx        ZX-UX cassette tape, internal name galaxian
  FONT-SOURCE.txt     font origin, changes, and license URL
  SCREENSHOTS/        real ZX-UX emulator captures from C48 execution

To play: boot the frozen beta-0.2.0 ZX-UX system, attach galaxian.tzx
as the program cassette and load/execute its internal name galaxian
using the normal ZX-UX cassette process (including the user's yolo
workflow). The file is a C48 SSX tape, not a ROM BASIC tape.
Press any key on the introduction to start. Z = left, X = right,
M = fire. The game supports enemy movement and lasers, explosions,
score, high score, and restarting after a hit.

Build: compile galaxian.c with the frozen sdk/bin/rcc, which also
assembles the matching galaxian.asm and links an SSX. The frozen
rtap.records and rtap.write routines package the SSX into the TZX.
No frozen ZX-UX source or tools are changed. The assembler draws
8x8 font and enemy glyphs directly into screen memory, without
claiming any UDG slots from the game.

Checks performed on the frozen beta-0.2.0 SDK and system:
  Source translated: yes; C48 compiled and linked: yes.
  TZX built: yes; tape headers and SSX1 record checked: yes.
  ZX-UX runtime: yes, via the frozen rvm emulator using a complete
  ZX-UX system tape generated in an isolated disposable build.
  Intro capture: SCREENSHOTS/01-C48-INTRO.png; headless run stopped
  while waiting for a start key after 287 emulated frames.
  Gameplay capture: SCREENSHOTS/02-C48-GAMEPLAY.png; Space was
  pressed and the running display captured after the 160-frame limit.
  Firing capture: SCREENSHOTS/03-C48-AFTER-FIRE.png; Space, X, Z,
  and M were sent; the display showed SCORE:10 after the 450-frame
  limit. All captures were taken from actual ZX-UX emulator runs.

Reference for comparisons: ../BASIC/KEYS-AND-TIMING.TXT and
../BASIC/SCREENSHOTS/01-INTRO.png, 02-MAIN.png, 03-AFTER-INPUT.png.
The original FUSE session ran at 320% speed, and its selected captures
occur at 15.965, 21.955, and 24.949 seconds from runner startup.
Those times include original BASIC load and RUN. They do not directly
apply to running a compiled ZX-UX executable. Compare matching screen
states, not wall-clock positions. The intro, six-ship fleet, descending
enemies, player base and score display have been observed in C48.

Known differences / remaining verification:
  * Text is intentionally Acer VGA 8x8, not Spectrum ROM font.
  * C48 uses its own pseudo-random sequence and integer positions;
    enemy positions are not deterministic matches to a BASIC session.
  * Some pixel collision checks from BASIC POINT and string slices
    are approximated with C48 sprite positions and flags.
  * The BASIC BEEP pitches and durations use the frozen SDK and
    timing can differ. Fire and explosion sounds have not been
    measured against the original recording.
  * Full behavioral equivalence (all hit/restart/fleet cycles) is
    not yet proven by the three short emulator runs.
  * A physical machine/FUSE cassette loading test using yolo has
    not been completed; ZX-UX rvm executed the compiled SSX instead.

The source is an experimental port, not yet verified for every game state.

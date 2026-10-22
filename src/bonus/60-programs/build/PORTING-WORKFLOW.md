# BASIC-to-C48 porting workflow — v0.1

This is the repeatable process developed while porting **25-galaxians** and
**58-invaders**. It is a procedure and an acceptance checklist, not a claim
that those two pilots have completed every gameplay-equivalence test.

Run commands below from \`src/bonus/60-programs/\` unless otherwise noted.
\`NN-name\` means the numbered program directory; \`game\` is its C48
source/tape stem (maximum 10 characters).

## Ground rules and output layout

- The frozen ZX-UX platform (beta-0.2.0) is read-only. **Only**
  \`src/bonus/60-programs/\` may be changed. In particular, do not alter
  the compiler, assembler, linker, SDK, kernel, emulator, root scripts,
  \`build/\` or \`dist/\` outside this workspace, even to fix a port.
- Preserve existing historical \`BASIC/\` listings, TZX tapes, replay
  records, and screenshots **byte-for-byte**. New work goes into
  \`NN-name/C48/\`, shared sources into \`c48lib/\`, and scripts into
  \`build/\`.
- The only canonical permanent storage is the private GitHub repository.
  Read the live \`main\` HEAD before work and before a push. No force-push,
  tag operations, or unrelated edits.
- Do not run full repository build/release in the canonical checkout:
  it regenerates frozen paths. Run frozen SDK tools with outputs inside
  the permitted workspace, or in an isolated disposable checkout.

Expected files for a port:

\`\`\`text
NN-name/
  BASIC/                  original, unchanged
  C48/
    game.c                translated program logic
    game-glyphs.asm       program-specific 8x8 sprites, if needed
    game.ssx              built ZX-UX executable
    game.tzx              built ZX-UX cassette
    README.TXT            controls, differences, tests, remaining gaps
    SCREENSHOTS/          actual captures only
c48lib/
  c48lib.asm              shared 32x24 screen renderer and key helpers
  c48lib-font.asm         Acer VGA 8x8 font data
  c48lib.h                declarations
  FONT-SOURCE.txt         font license and attribution
build/
  build-c48.py            numbered-order compilation and tape packaging
  test-c48.py             CURRENTLY covers pilots 25 and 58 only
  build-basic.py          optional fresh BASIC reference tape/replay builder
  tmp/.gitkeep            tracked placeholder; generated contents ignored
\`\`\`

The assembler does not support INCLUDE, and \`rcc\` links a matching
same-basename \`.asm\` file automatically. \`build-c48.py\` constructs that
companion **only in \`build/tmp/\`** by combining the shared renderer, font,
and local glyphs. Do not commit generated \`game.asm\` files.

## Step-by-step procedure and checks

### 1. Inspect the original program; record the contract

Read \`BASIC/NN-name.bas\` from beginning to end. Also read
\`BASIC/README.TXT\`, \`KEYS-AND-TIMING.TXT\`, \`REPLAY.sh\`, and the
original \`BASIC/SCREENSHOTS/\` images. Inspect the original TZX if tape
behavior is relevant. Record:

- Every playable state: intro, initialisation, main loop, win, lose,
  restart, levels and special animations.
- Controls and **their exact BASIC implementation** (\`INKEY$\`,
  \`IN\` port reads, cursor/shift combinations, \`PAUSE\`, \`INPUT\`).
- Rules: movement, collision detection, obstacles, score/high score,
  lives/ammunition, random behaviour, boundaries, timing and sound.
- Print and drawing commands: rows/columns, pixel coordinates, paper,
  ink, border, \`OVER\`, \`INVERSE\`, \`FLASH\`, \`PLOT\`, \`DRAW\`, etc.
- \`DATA\`/\`READ\`/\`POKE\` and UDG definitions, including order in which
  bytes are assigned to character cells.

**Check:** Keep a short BASIC-line-to-C48-function mapping or equivalent
notes. Nothing essential may disappear merely because it is difficult to
port. Mark undecoded constructs and unclear game rules explicitly.

### 2. Establish authentic BASIC visual/behavioural references

Use the **existing historical** BASIC TZX and selected FUSE screenshots
as the primary reference. When useful, run that original tape in a
Spectrum 48K/FUSE and capture intro, active gameplay, an interaction,
a hit/miss, and an endgame. Save any new experimental captures separately.

Optional: \`python build/build-basic.py --screenshots NN-name\` generates
a **new** tape from the stored \`.bas\` listing and fresh FUSE captures in
\`build/tmp/basic-output/\`; it must not overwrite the originals.
The re-tokenised tapes are **not byte-identical** to the historical
tapes and are secondary evidence only.

**Check:** Confirm genuine source provenance. Compare the same game
*states*, not blindly the same elapsed seconds: historical FUSE times
include tape loading and can use a different emulator speed; animations
and random seeds can also change individual frames.

### 3. Verify the frozen target and port constraints

Read the actual frozen \`c48.h\`, SDK examples and implementation of any
API you intend to call. Establish the target's C48 restrictions,
calling convention and RAM budget. Use only verified compiler/runtime
interfaces. Do not infer that a Sinclair ROM BASIC function is available
to a C48 program.

**Check:** List any unavailable BASIC facility and the port-local
replacement. If no legal replacement exists, report a blocker. Never
patch \`rcc\`, \`ras\`, \`rld\`, \`libc48\`, the kernel, or the emulator.

### 4. Transcribe and independently verify game graphics

For each historical UDG or \`POKE USR\` glyph, extract all **eight**
bitmap bytes from BASIC \`DATA\` and reconstruct any interleaved
\`READ\` layout correctly. Put the game's data in
\`C48/game-glyphs.asm\`. The shared \`c48lib\` renderer uses glyph
codes **32..127** for the VGA font and **128..159** for local graphics;
map original BASIC character codes deliberately. Do not reserve or
overwrite frozen SDK UDG slots.

**Check:** Independently reconstruct the BASIC bytes and compare them
to the port's table, glyph by glyph. The pilot test script checks both
Galaxians' contiguous sprite data and Invaders' interleaved data.
Visually inspect large/multi-cell sprites assembled from those glyphs.

### 5. Translate the real gameplay, screen and sound

Create \`C48/game.c\`: translate original state and rules, not a
substitute game. Preserve screen geometry (32 columns by 24 rows for
shared full-height text), controls, palette, ship/enemy/shield layouts,
movement and redraw behaviour, scoring and transitions. Use shared
\`c48_cell()\` for text/sprites, existing frozen pixel APIs for pixel
drawing, and C48 sound/timing APIs where justified.

Where BASIC checks \`SCREEN$\` or \`POINT\`, model the correct logical
characters and/or bitmap state rather than guessing from a nearby
sprite. Track moving objects and erase **their previous positions**.
Galaxians' mothership trail and Invaders' overlapping HUD text are
examples of the failure mode.

**Check:** For every main BASIC branch and subroutine, identify the
corresponding C48 path. List deliberate differences (font, timings,
randomness, sound, controls, collision precision). No silent changes.

### 6. Handle keyboard semantics deliberately

BASIC \`INKEY$\` is a nonblocking view of *current* Spectrum keys; it
is not equivalent to buffered terminal \`getchar()\`. For gameplay,
use verified physical-key state, such as \`kbd_down()\` and shared
\`c48_any_key()\`. For CAPS SHIFT cases use the verified shared
\`c48_shift_down()\` (Invaders uses SHIFT+5/8 for five-cell moves).
Set the ZX-UX terminal to raw, non-echo mode using frozen
\`gtty\`/\`stty\` when the game polls keys directly.

For a new-press-only intro/restart prompt, use a defined sequence:
wait until all keys are **released**, wait for a **fresh press**,
then wait for **release** before gameplay resumes. Review whether that
release policy intentionally differs from a specific BASIC prompt.

**Check:** Test no key, a short tap, a held key, release/repress,
rapid fire, shifted movement, and a game-over prompt after sustained
gameplay. A previously held or buffered gameplay key must not dismiss
a new prompt. A key must not echo unwanted characters onto the screen.
The initial shared keyboard-scanning loop once failed to terminate
with no key; this was caught by the emulator and fixed, so idle-key
testing is mandatory.

### 7. Build with the frozen SDK; keep intermediates temporary

From the workspace root:

\`\`\`sh
python build/build-c48.py NN-name
\`\`\`

Use \`--sdk PATH\` only if the frozen SDK is elsewhere. The builder:

1. Copies the C48 source and headers to mirrored \`build/tmp/\` paths.
2. Concatenates \`c48lib.asm\`, \`c48lib-font.asm\` and
   optional \`game-glyphs.asm\` into a generated matching \`game.asm\`.
3. Calls frozen \`rcc\` to compile, assemble and link an SSX.
4. Uses frozen \`rtap\` to package the executable as a TZX.
5. Copies **only** \`game.ssx\` and \`game.tzx\` into \`C48/\`;
   cleans intermediates on success and preserves them for debugging
   on failure.

With no arguments, it builds the *available* ports in historical
directory order 01 through 60. The executable tape name must fit the
10-character limit.

**Check:** Distinguish each outcome: translated source, compiled,
linked, SSX created, TZX packaged. Verify the intended tape's internal
name and that its SSX/TZX exist. A successful build is **not** proof of
ZX-UX runtime execution, \`yolo\` loading or BASIC equivalence.

### 8. Make a first independent source-review pass

Review \`.bas\` and \`.c\` side by side without relying on the port
author's description. Compare line mapping, constants, indexes,
\`DATA\` sprites, collision state, key semantics and exit/restart paths.
Look specifically for off-by-one errors, shifted characters, misread
\`BIN\` data, wrong arguments to pixel functions, unsigned arithmetic,
and stale screen contents.

**Check:** Resolve all substantive discrepancies or record blockers.
Prefer a different reviewer/agent when available; independence means
re-checking against BASIC, not merely reading the author's notes.

### 9. Execute under the *real frozen ZX-UX kernel*

Boot an actual frozen ZX-UX system image using the existing \`rvm\`
emulator (or an equivalent supported real-machine session). Provide
the matching system TZX and \`kernel.json\`, not merely a standalone
assembled graphics proof. Exercise startup, input, gameplay and visible
state transitions.

The existing pilot regression is:

\`\`\`sh
python build/test-c48.py --system /path/to/ZX-UX.tzx --sdk /path/to/sdk
\`\`\`

\`--captures\` additionally writes actual emulator frames into pilot
\`C48/SCREENSHOTS/\`: use it only when intentionally updating evidence.
**Without \`--system\`, \`test-c48.py\` runs source checks only and says
that emulator tests were skipped.** Its assertions currently cover
programs 25 and 58; extend tests for each new port before treating
this as a universal gate.

**Check:** Confirm the process starts under ZX-UX and the program
responds correctly to actual key events. Save only genuine, labeled
captures. Compare intro and equivalent animated/gameplay states
against the original BASIC images. A direct SSX run does **not**
establish that \`yolo\` can load the TZX; test \`yolo\` separately before
claiming that loader path works.

### 10. Run a separate adversarial behavioural pass

Try to *break* the port after the ordinary path passes. Deliberately
exercise:

- Idle, tap, hold, release and rapid repeated keys; game-over restart
  without a new press; terminal echo and shift/cursor combinations.
- Every scoring case, valid hit, miss, simultaneous events, projectile
  flight, moving target, ship destruction, shields, edge columns,
  lives/ammo exhaustion, victory, defeat, replay and high scores.
- Sprite redraw trails, overwritten/ghost HUD characters, incorrect
  colour attributes, screen-edge drawing, stale object-grid state,
  accidental ASCII characters used in place of game glyphs.
- Timing-dependent sequences: early fire, late fire, multiple levels,
  random spawns and collision near boundaries.

The pilot adversarial pass found an endless idle-key scan, an ASCII
\`a\` in place of a rocket, invisible projectile travel, score-line
remnants and inaccurate command-ship hit accounting. These faults
illustrate the value of trying **negative** conditions as well as
successful play.

**Check:** Each confirmed defect gets a minimal code fix and a
repeatable assertion that fails on the old behaviour. Rerun normal
and adversarial tests after fixing. Do not count timed-out tests as
passes; do not claim complete gameplay equivalence from one screenshot.

### 11. Rebuild twice and preserve useful evidence

Run the same build twice without source changes; compare the resulting
SSX and TZX hashes. Check \`build/tmp/\` contains only its tracked
\`.gitkeep\` after success. Keep original \`BASIC/\` files and their
screenshots unchanged. Store actual C48 captures, control instructions,
known differences, test commands and unresolved outcomes in
\`C48/README.TXT\` (and \`C48/SCREENSHOTS/\` as appropriate).

**Check:** Byte-for-byte reproducibility, no generated \`game.asm\`
tracked in Git, no unintended writes outside the workspace. Run the
available private checker on candidate files where accessible; never
alter the checker to manufacture a pass.

### 12. Inspect, commit, push and verify the remote

Before publishing, re-read live remote \`main\` and reconcile any
intervening work. Review the **complete** proposed diff, including
added, modified, removed and renamed files.

**Hard reject** if a changed path lies outside
\`src/bonus/60-programs/\`, or if an original historical file was
changed without explicit authorization. Stage only the requested
port/test/doc files. Use a fast-forward update; never force-push.
Read back the remote HEAD, commit/tree and changed-path list after
the push; report any failed check or upload.

**Check:** The verified remote commit contains exactly the approved
paths and test evidence. Do not claim a push before remote read-back.

## Completion record (copy into each port's README)

Use **PASS / FAIL / NOT RUN / NOT APPLICABLE**, with actual evidence or
a short explanation for each line:

\`\`\`text
[ ] Original BASIC rules/controls/screen inventory completed
[ ] BASIC UDG/DATA sprites independently compared
[ ] BASIC visual states/reference captures identified
[ ] C48 source translated and independent review passed
[ ] Frozen C48 compiled
[ ] Frozen assembler/linker produced SSX
[ ] Frozen tape packager produced TZX; internal name checked
[ ] Actual ZX-UX execution demonstrated (system image recorded)
[ ] Actual C48 screens captured and visually compared to BASIC
[ ] Start, idle-key, hold/release, restart and keyboard-mode checks
[ ] Movement, scoring, hits, misses, boundaries and HUD checked
[ ] All relevant win/loss/replay, special animations and sound checked
[ ] Independent adversarial review passed
[ ] Relevant regression assertions added and passed
[ ] Repeated builds byte-for-byte equal; temporary files cleaned
[ ] yolo loaded and executed final TZX (if claiming yolo support)
[ ] Historical BASIC and frozen platform unchanged
[ ] Private checker available: result recorded
[ ] Remote GitHub fast-forward push and read-back verified
Open differences / tests not run:
Evidence paths / commands:
Verified remote commit:
\`\`\`

**Language for reporting:** State *source translated*, *compiled*,
*linked*, *tape generated*, *ZX-UX executed*, *visuals compared*, and
*behaviour independently verified* separately. A program with an
unexercised relevant gameplay branch remains an **experimental port**;
never label it fully verified solely because it compiles or boots.

## Pilot status when v0.1 was written

- **25 Galaxians:** BASIC sprite-data review, compilation/linkage,
  tape creation, real-kernel intro/gameplay, stable game-over prompt
  and fresh restart have evidence. The fleet-completion mothership
  animation, exhaustive collisions/sounds and \`yolo\` tape loading
  remain open.
- **58 Invaders:** BASIC sprite-data review, compilation/linkage,
  tape creation, real-kernel launch, movement, visible rocket flight,
  a 20-point alien hit, a -10-point miss, clean HUD and CAPS SHIFT
  movement have evidence. A real 200-point command-ship hit, every
  victory/defeat/replay path, full sound/collision fidelity and
  \`yolo\` tape loading remain open.

This is **v0.1**: update the procedure when a new port uncovers a
repeatable gap, but never retroactively promote unrun tests to passes.

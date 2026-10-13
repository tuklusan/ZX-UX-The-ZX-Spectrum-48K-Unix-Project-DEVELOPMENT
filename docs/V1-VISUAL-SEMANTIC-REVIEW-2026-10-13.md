# ZX-UX v1 semantic screenshot review — 2026-10-13

Source snapshot: private `tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project`, `main` commit `aba89436ff12d7834bf7a2c44d24340db8699557`. This is a **visual-review milestone, not final release approval**. An authenticated GitHub connector supplied the images and sources. No screenshot was invented or redrawn.

## Recorded paths and hashes

The 48 old-SDK PNGs are `docs/visual-reference/old-sdk/<category>/<program>.png`. Their verified historical SHA-256 values, historical source paths and hashes are per-case records in `docs/step5-v1-frame-comparisons.json`. The v1 screenshots actually inspected here are `release/shots/<program>.ZX-UX.png`; their **current release** SHA-256 values and byte sizes are in `release/manifest.txt`. These two indexed records together bind the full old/new path and hash to **each named case below**. Avoid using the JSON's older `build/shots/` hashes as current-release hashes: 23 of its 48 new screenshot hashes differ from the current release manifest, consistent with recapture or frame changes. PNG comparisons below were based on the actual remotely stored pixels, not the old pixel-difference counts.

The separate 30 old-kernel PNGs are at `v1/dist/media/P11.pre-release/sdk/proof/visual/<category>/<program>.png` in private `tuklusan/ZX-UX-old-abandoned`. Each has a matching `.scr`. Their per-program capture frames, PNG and SCR SHA-256 hashes and the exact 6,912-byte SCR lengths are recorded in `v1/dist/media/P11.pre-release/sdk/proof/native-visual-run.json` in that historical repository. All 30 PNG files were visually inspected and all 30 SCR files were fetched and independently length-checked as 6,912 bytes. The old-kernel capture state is often a title-only early frame and does not prove identical execution with v1.

Status rule: **PASS** means the inspected image semantically depicts a plausible stage/output of the named program, not frame identity or full functional conformance. **FAIL** means a proven wrong-program image or defect in the comparison record. **INCONCLUSIVE** means the captured subject cannot be verified. Different animation frames, valid random outcomes and partial terminal drawing are acceptable.

## 48 old-SDK PNG vs v1 native screenshot reviews

| Program | Result | Actual observed content |
| --- | --- | --- |
| apps/gp82 | PASS | Grand Prix 1982 bar and pie charts in both; layout matches |
| apps/sheet48 | PASS | 1992 home brokerage allocation spreadsheet |
| apps/wire3d | PASS | Imperial cruiser wireframe and perspective grid |
| apps/write48 | PASS | Sinclair resume editor and matching text |
| demos/city | PASS | Multicolored vector buildings and roadway |
| demos/dizzy4k | PASS | Yellow cartoon hero with red limbs and eyes |
| demos/firework | PASS | Colored fireworks above outlined buildings |
| demos/forest | PASS | Branching multicolored fractal trees |
| demos/galaxy | PASS | Four-arm starfield and spiral core |
| demos/goblet | PASS | Wireframe goblet shape |
| demos/hanoi | PASS | Three pegs and disks all on the destination peg; solved text |
| demos/julia | PASS | Multicolored Julia fractal with caption |
| demos/kaleido | PASS | Eightfold mirrored line pattern |
| demos/mandel | PASS | Multicolored Mandelbrot-like fixed-point pattern |
| demos/mobius | PASS | Multicolored one-sided loop wireframe |
| demos/moire | PASS | Two overlapping concentric interference patterns |
| demos/morph3d | PASS | Concentric cube-to-star wireframe |
| demos/ocean | PASS | Blue background, wave mesh and moon |
| demos/orrery | PASS | Nested colored planetary orbit loops |
| demos/plasma | PASS | Colored tiled attribute pattern |
| demos/queens8 | PASS | Blue chessboard with eight white queens and solution-found text; not Hanoi |
| demos/raymaze | PASS | Red and magenta/green column raycast corridor |
| demos/spriteanim | PASS | Small yellow walker against a starfield |
| demos/sprites | PASS | Four colored fleets of little sprites in a starfield |
| demos/terrain | PASS | Colored mountain height-grid wireframe and moon |
| demos/torus | PASS | Colored wireframe torus |
| demos/tunnel | PASS | Nested multicolored twisting polygon tunnel |
| demos/warp | PASS | Multicolored short star streaks |
| examples/argv | PASS | Two-column printable argument and character examples |
| examples/colors | PASS | Normal and bright Spectrum color test bars |
| examples/graphics | PASS | White circles with two crossing diagonal lines |
| examples/hello | PASS | Hello message; v1 captured while the next line was still printing |
| examples/maze | **FAIL** | Historical example shows diagonal lines and a 1982 caption. The current screenshot belongs to the separate games/maze program and shows its playable wall grid. This capture does not verify execution of examples/maze. |
| examples/udg | PASS | Space-invader-style UDG sprite; v1 is an earlier partial-draw frame |
| games/advent | PASS | Stone cabin and adventure prompt |
| games/arith | PASS | Arithmetic question with differing valid random operands |
| games/bgammon | PASS | Text backgammon board and dice |
| games/chess | PASS | Colored chess setup; one capture includes later side-selection prompt |
| games/cribbage | PASS | Card discard prompt with differing deal |
| games/fish | PASS | Go Fish hand counts and prompt with differing cards |
| games/fortune | PASS | Fortune text and repeat prompt, with different random saying |
| games/hangman | PASS | Gallows and blank word |
| games/maze | PASS | Interactive solid-wall maze with start and exit |
| games/quiz | PASS | ZX Spectrum CPU multiple-choice question |
| games/rogue | PASS | ASCII dungeon map, gold and HP |
| games/snake | PASS | Bordered snake playfield with food and score |
| games/trek | PASS | Short-range scan and starship status |
| games/wump | PASS | Hunt the Wumpus rooms, tunnels and arrows |

**Old-SDK semantic result: 47 PASS, 1 FAIL (capture mapping).** No v1 runtime failure is inferred from the mapping error alone. Pixel matching is not a requirement and the prior unmatched pixel-difference results must not be restated as behavioral failures.

The single old/new source mismatch is `games/fortune.c`: one backup/restore saying was rewritten in the current source. The inspected program still displays randomized fortunes and accepts the same prompt controls. This is a wording/source difference, not a wrong-program visual. The old source was inspected read-only in the owner-supplied historical SDK ZIP.

**Root cause of the maze capture error:** `programs/c48/examples/maze.c` draws diagonal lines and prints `1982 called. it wants its maze back.` while `programs/c48/games/maze.c` draws the playable grid. `sdk/tests/runs.json` has a single `maze` key pointing to `games`; the shipped `release/shots/maze.ZX-UX.png` is the game image. Release filenames keyed only by basename cannot independently represent both programs. Fix by using directory-specific identities through the scenario selection, output paths, screenshot capture and release manifest; compile and capture both programs independently. Review every filename-dependent caller and rerun release tests. Do not relabel the games screenshot as the examples screenshot.

## Separate 30 old-kernel native PNG/SCR reference reviews

All old-kernel outputs below are genuine PNG/SCR pairs from the retired historical repo. Their early native captures mostly contain only the program title, whereas current v1 screenshots show fuller or later graphics. The old-kernel observations are **semantic subject checks only**, not proof of matching program state or complete visual execution.

| Old-kernel case | Subject review | Actually visible old-kernel content |
| --- | --- | --- |
| examples/argv | PASS | Spectrum Unix argument text fragment |
| examples/colors | PASS | Spectrum attribute test title |
| examples/graphics | PASS | `c48 graphics` title |
| examples/hello | PASS | `hello from c48` text |
| examples/maze | PASS | `1982 called. it wants its maze back.` caption; confirms the separate example identity |
| examples/udg | PASS | `udg sprites` title |
| demos/city | PASS | Vector metropolis title |
| demos/dizzy4k | PASS | `START A STORY...` intro card; independently confirmed as a valid `intro_text()` caption in current source |
| demos/firework | PASS | Firework night title |
| demos/forest | PASS | Fractal forest title |
| demos/galaxy | PASS | Spiral galaxy title |
| demos/goblet | PASS | Crystal goblet title |
| demos/hanoi | PASS | Towers of Hanoi title |
| demos/julia | PASS | Julia ballet title |
| demos/kaleido | PASS | Kaleidoscope title |
| demos/mandel | PASS | Mandelbrot dive title |
| demos/mobius | PASS | Mobius wireframe title |
| demos/moire | PASS | Moire engine title |
| demos/morph3d | PASS | Polyhedron morph title |
| demos/ocean | PASS | Ocean grid title |
| demos/orrery | PASS | Clockwork orrery title |
| demos/plasma | PASS | Spectrum plasma title |
| demos/queens8 | PASS | Eight Queens title, not Hanoi disks |
| demos/raymaze | PASS | Raycast labyrinth title |
| demos/spriteanim | PASS | Walker animation title |
| demos/sprites | PASS | Sprite storm title |
| demos/terrain | PASS | Mountain flight title |
| demos/torus | PASS | Torus reactor title |
| demos/tunnel | PASS | Infinity tunnel title |
| demos/warp | PASS | Warp drive title |

**Old-kernel subject review: 30 PASS, 0 wrong-program titles.** Full graphics/frame equivalence remains INCONCLUSIVE because these historic screenshots were captured before most drawing completed. Do not copy old executable formats or restricted archive material into v1.

## Open release gate

The `examples/maze` screenshot and potentially its execution coverage must be corrected and actually retested; add distinct directory-specific capture records. Rebuild from a clean current-HEAD source checkout, run all required new-revision gates including actual FUSE tape boot, then update and verify the tracked release manifest and all affected captures. The last full passing report relates to source `1445b3b27ad4790cd88923316c95accd853a01b3`, not the later `main` revision above. This review did not execute a new full release build.

LM remains an approved compilation-only exception; its non-execution is **not** a release blocker. A physical ZX Spectrum test was not requested. The repository and release remain private pending final release approval.

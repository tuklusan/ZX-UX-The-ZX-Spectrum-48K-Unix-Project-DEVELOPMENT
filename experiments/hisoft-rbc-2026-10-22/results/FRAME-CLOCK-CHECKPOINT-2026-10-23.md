# RBC frame-clock milestone — 2026-10-23

Repository: `tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT`
Branch: `main`

## Source references and saved test records

- Compiler-side frame-clock implementation: commit `35c9cdb7df5cb1ffc5e44a37c7f9583119c5cedc`; file `experiments/hisoft-rbc-2026-10-22/stage/process_frame_clock.py` (Git blob `25b3b741713d3b177c6123f70135a8aa31e09422`).
- Real-emulator timer probe and strict advancing-tick assertion: commit `ab70cc296464e5d009cb21953fc5fb2866f139e1`; `experiments/hisoft-rbc-2026-10-22/stage/frame_clock_native_probe.py` (Git blob `58a5303482694a9d86c173859c2364c9c2fbf971`).
- Complete 121-input results: `experiments/hisoft-rbc-2026-10-22/results/LATEST-RBC-FULL.json`, saved with main commit `cbdb74b68a7667f07e32dab5ae9e1d40c270a3b5` (Git blob `ceaa3192e32ed538f720996981e0f8c82d7ba4f7`); execution run ID `40011182974`, source revision `ab70cc296464e5d009cb21953fc5fb2866f139e1`. Read this historical Git blob/commit rather than assuming the mutable LATEST file will remain identical.

## Verified results from the saved run

- Whole collection: 105 of 121 source inputs compiled; all 121 have saved input records. This is the compilation score only. It does not mean 105 programs passed native gameplay.
- `06-motocross`: original `.bas` and `.tzx` inputs both compile; tape executable starts under the frozen ZX-UX emulator, shows a nonempty screen, and changes the screen during the timer probe. Over 4,800 emulated frames the CPU hook recorded 8 calls to kernel service 38 after foreground start, with 8 distinct returned tick values: 3413, 3630, 3881, 4098, 4320, 4552, 4793, 5020. The recorded timer assertion passed.
- `32-buzzy-bee`: original `.bas` and `.tzx` inputs both compile; tape executable starts, shows a nonempty screen, and changes the screen during the timer probe. Over 4,800 frames the CPU hook recorded 24 calls to service 38 after foreground start with 12 distinct returned tick values (first 3591; last 6206). Repeated values occur when multiple reads happen within a frame. The recorded timer assertion passed.
- Clock implementation uses the kernel's 50 Hz tick service, with timer state in process memory. The original writes to the shared Spectrum frame-counter bytes are handled by compiler-generated code rather than direct global writes. The original BASIC and tape files remain byte-for-byte unchanged. No frozen SDK, kernel, emulator, or beta release files were altered for the fix.

## Boundaries and remaining work

- Passing the timer probe proves that the native kernel service is called and returned tick values advance. It does not by itself prove all elapsed-time calculations, timer wraparound during an actual long run, input sequences, gameplay end states, screen comparisons, or restart behavior. Unit tests separately cover the compiler-side timer arithmetic and input guards.
- Five previously compiled tape executables still fail native launch with `not enough memory`; this milestone does not resolve that loader constraint.
- Track A: 105/121 compiled inputs, with native execution, complete state checks, and remaining inputs still open. Track B: 3/60 C48 ports accepted (`01-minelay`, plus pilots `25-galaxians` and `58-invaders`); next regular port `02-fall-guy`. Track B acceptance is independent of Track A.
- Keep the full per-input results and failures in GitHub. Continue addressing the largest remaining common cause without modifying the original 60 BASIC text/tape pairs, the frozen release, or private checker rules.

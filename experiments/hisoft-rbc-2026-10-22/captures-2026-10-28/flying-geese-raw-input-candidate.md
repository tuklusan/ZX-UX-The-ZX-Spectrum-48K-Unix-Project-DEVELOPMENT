# Bounded raw INPUT experiment — real ZX-UX, 2026-10-28

**Experimental source only. Production RBC and all published SSX files remain unchanged.**

The original Flying Geese game was compiled from untouched BASIC with the
three-base verified HiSoft source. Its original pre-link ROM EDITOR call was
substituted in the independently assembled source (never a linked SSX) with
an experimental ZX-UX raw-terminal reader. `ras` assembled it and `rld`
linked it. All relative words are checked at three separate load bases.

The reader uses the original kernel `_gtty`, `_stty` and `_read` system calls,
and Spectrum ROM `$1652` for one-character BASIC workspace insertion. It
restores the original terminal mode on return, bounds the BASIC workspace
below the low kernel at `$5D98`, handles DELETE, and **discards excess keys**
without aborting the running program. These are measured candidate behaviors,
not proof of full Sinclair INPUT semantics. In particular, ordinary ROM
screen editing, visible input echo and all control codes have not passed.

A real 48K ZX-UX/Z80 replay used the original `39-flying-geese.bas`, sent
130 physical `A` key events and then ENTER after 150 frames. The emulator
observed `GAME OVER` with the 100-shot score, followed by a new native game
board with the game-over text gone. Both PNGs are copied directly from the
emulator's genuine 6,912-byte framebuffer. They have not been retouched.

| Original or test image | Bytes | SHA-256 |
| --- | ---: | --- |
| Original BAS | 2,858 | `94cda828f926c95cb1b74803c471d7a28c0c9091d4a93e3a22f52919efbe731a` |
| Original TZX | 2,989 | `a416c968ce4026622887d6adcd4f85d87c1d72319944ee243d52d2b512a75674` |
| Published SSX | 8,526 | `920fef840c85b84e290b2c3f1818017f79b0661a5751af91e75233675eafedb2` |
| Unpublished raw candidate SSX | 8,777 | `b90f5de1f7a83c839b0ba8dd294c3a8bc208530625bcb6dc48760cbee5fb8923` |
| `flying-geese-raw-gameover.png` | 3,860 | `9a0a1edb288f7e4e3e2ca7ae1b769ece1c349a1ea339840741d84257d63219c8` |
| `flying-geese-raw-replay.png` | 2,765 | `d72f5da71aef28fe77e88ca21f0a48681dd654b76953468fefbb92c2341a58fa` |

The candidate linked image is 7,779 bytes, BSS 501 bytes, stack 384 bytes,
8,664 bytes combined, with 976 relocation entries. Both image total and
8,777-byte SSX file fit the 14,000-byte loader limit. These values do not
claim production admission of the new reader.

The source-level test runs string and numeric INPUT, DELETE, input beyond the
canonical 79-key terminal limit, the bounded ROM workspace, two sequential
native processes with shell/system-state restoration, and source witness
rejection. Separate real-emulator tests advance original Minelay and Space
Traffic with this candidate. Existing ROM syntax, dual-source, native CLI,
STOP/shell and earlier INPUT isolation suites were rerun. Original BAS, TZX,
ROM, kernel and 34 published SSX files were not changed.

Reproduce from the checked repository root with the reconstructed compiler
and frozen 48K ZX-UX kernel:

```sh
export RBC_FRONTEND_DIR="$PWD/build/tmp/rbc-inputs/upstream-pyhsb"
export RBC_HISOFT_TAPE="$PWD/build/tmp/rbc-inputs/hisoft48.tap"
export RBC_RAW_GEESE_CAPTURE_DIR="$PWD/experiments/hisoft-rbc-2026-10-22/captures-2026-10-28"
python3 -B -m unittest discover \
    -s experiments/hisoft-rbc-2026-10-22/tests \
    -p test_native_input_raw_candidate.py -v
```

Kernel tape SHA-256: `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597`.
Original 48K ROM SHA-256: `d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42`.

**Release blocker:** The raw editor does not yet establish all ROM editing,
error and numeric-input semantics, 120-source BAS/TZX byte-equal builds,
production memory/safety gates, or gameplay for all 34 games. The existing
production Flying Geese replay remains unverified. No replacement SSX is
published by this experiment.

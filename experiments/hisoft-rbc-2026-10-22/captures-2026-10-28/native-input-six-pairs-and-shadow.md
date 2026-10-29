# Bounded ZX-UX INPUT source checks — 2026-10-29

The original published ZX-UX loader and all game SSX files remain unchanged.
The RBC CLI's default remains the witnessed original ROM EDITOR path. An
explicit `--input-backend zxux` option emits a different, source-level,
relocatable INPUT path. This is not approved as a production replacement: the
full Spectrum ROM editing controls and error cases still lack proof. The
revised source echoes printable keys and erases the last character on DELETE.
It uses native `ras` and `rld` without an optimizer or linked-file patching.

The checked `tests/native_input_six_pairs.py` independently decodes each
original TZX BASIC listing, validates its tokens against the BAS listing, then
builds BAS and TZX separately with identical no-optimizer CLI options. Six
pairs linked and matched byte-for-byte. Every result was below the default
14,000-byte loader limit, with three-base relocation checked in the source
build. These test images remain under untracked `build/tmp`, not in game `bin/`.

| Original game | Input-side SSX bytes | SHA-256 (identical BAS and TZX outputs) |
| --- | ---: | --- |
| 01-minelay | 11091 | `f14ac9451df79a38e605ea457e1a7fda8398e4336d566c1cc249e21ac2e456c6` |
| 07-critical-path-analysis | 11917 | `60018e1ca0a7e46a897cc70260bc08a89e790c55d35d0e9e2a57078f7fd95420` |
| 23-biorhythms | 8572 | `7d26d20444c5607de29973de6d491704507c88b411ced48207ce352432ba0c4f` |
| 30-space-traffic | 10827 | `f3a5ee9d186909de125b5c7609e71904c1216bbff374dd5416c65a759d0ae481` |
| 39-flying-geese | 8793 | `e13aea95d21540757c2d4b8c8859aed8fb2c9b918a0ff57ec06df219659fee97` |
| 56-roots | 11316 | `facdd940e4510bf5f186398655ca6528bb7b619b2ddd231b3384a59b8f93953e` |

The genuine ZX-UX Z80 tests of these temporary images also observed Minelay
enter its maze, Critical Path's numeric input and invalid-finish reprompt,
Biorhythms and Roots responding to entered fields, and Space Traffic reaching
its game-over screen. A separate fresh emulator run of Flying Geese observed
100 shots, GAME OVER, ENTER and a new board. Printable input echo, DELETE
screen erasure, numeric correction, bounded ROM workspace and shell return
were checked with native temporary fixtures. These individual paths are not
proof of complete gameplay or every Sinclair editing feature.

The checked `tests/native_input_shadow_34.py` gives the real Z80 loader a
symlink-only *temporary* shadow of the 34 published games. Six paths use the
verified BAS-built candidates; the other 28 paths point to their unchanged
published SSX files. Original BAS/TZX paths stay read-only inputs. Each program
is booted once without keys and once with its source-guided physical keyboard
script at the same emulated-frame limit, with at most five parallel jobs and
a 2,400-second (40-minute) per-game timeout. Per-game stdout, stderr, exit
status and failed/partial results are retained under `build/tmp`.


## Completed real-Z80 34-game shadow run

With the six matched opt-in candidate pairs and 28 unchanged published SSX
files, the full 34-game shadow gate completed in seven bounded groups:
**34/34 screen differences, zero game-process errors or timeouts.** The
original production 34-game comparison was 29/34 differences and five
unverified INPUT responses. This is a *screen-response comparison* only,
not proof of all levels, wins, losses, every control or replay path. No
published production executable was replaced.

The complete terminal output was saved untracked under
`build/tmp/rbc-shadow-verified-run.log` (SHA-256
`016ceafeca4acefe1a057591b3d0867f4f7b852d0cb903ea429a0ee0ad9b2640`).
The independently rebuilt six-source comparison log is
`build/tmp/rbc-input-six-pairs-final.log` (SHA-256
`dec037acc28f06272ff3d31a38bf8ebe4ab8c1dd80a53a780e426a4028c94934`).
Both commands exited zero. The live native INPUT integration suite passed
8/8; the baseline native CLI passed 3/3, ROM syntax 6/6, original BAS/TZX
fidelity 10/10, STOP/shell lifecycle 3/3, and prepared-candidate
tampering/refusal tests 2/2. These results are local to the exact checked
source and original ZX-UX tape, not an assertion of total game coverage.

Each game has a separate stdout/stderr/exit log beneath the unique
`build/tmp/rbc-input-shadow-*` directory printed by the runner. A checked
nonzero exit or timeout is an explicit failure, never a pass. Reuse via
`--prepared` checks candidate output SHA-256, independent outcomes and
three-base native-link reports before launching the emulator.

**Screen differences do not establish wins, losses, all control paths, a
complete game, or full ROM INPUT equivalence.** The production HiSoft INPUT
path and published Flying Geese replay remain unresolved until a separately
approved source revision and full safety gates pass.

Reproduction from the repository root, with the recovered checked compiler,
original frontend/tape, frozen ZX-UX system and 48K ROM available:

```sh
export RBC_FRONTEND_DIR="$PWD/build/tmp/rbc-inputs/upstream-pyhsb"
export RBC_HISOFT_TAPE="$PWD/build/tmp/rbc-inputs/hisoft48.tap"
python3 -B experiments/hisoft-rbc-2026-10-22/tests/native_input_six_pairs.py
python3 -B experiments/hisoft-rbc-2026-10-22/tests/native_input_shadow_34.py --prepared
python3 -B -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests -p test_native_input_source_compiler.py -v
```

No RBC GitHub workflow was created. The 60 BAS originals, 60 TZX originals,
34 published SSX files, 26 existing failure READMEs, ROM and ZX-UX kernel were
not modified by these checks.

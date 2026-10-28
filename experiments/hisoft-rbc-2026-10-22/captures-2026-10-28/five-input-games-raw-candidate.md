# Bounded original INPUT game checks — raw pre-link source experiment

The experimental `native_input_raw_candidate.py` reader was assembled into
five unchanged original BAS games and tested using the real ZX-UX loader/Z80.
The linked experimental SSX images stayed under `build/tmp` or temporary
folders. Neither published game executables nor the original BASIC files
were edited. Three-base native relocation was checked before execution.

| Original game | Input script exercised | Real-kernel result |
| --- | --- | --- |
| Minelay | ENTER, ENTER, 2, Q | Score/maze display reached; running |
| Critical Path Analysis | Intro ENTERs, start node 1, invalid finish 0, valid finish 12 | Start prompt changes; 0 is rejected; 12 advances |
| Biorhythms | Six entered date fields | Input-state screen differs from no-input control |
| Space Traffic | ENTER, ENTER | Natural game-over display reached; running |
| Roots | Three ENTERs | Input-state screen differs from no-input control |

The raw reader separately passed source-witness rejection, numeric/string
input, DELETE, overlong line memory bounds, Flying Geese replay and
sequential process isolation. Scuba and Swordsman were tested separately
using their **unchanged published** SSX files and original `INKEY$` controls.
These seven focused paths address the seven unchanged final screens in the
generic keyboard batch. Some paths still use experimental replacements, and
none of these checks establish complete gameplay.

Reproduce the five-game batch with the checked compiler, ROM and original
ZX-UX system tape:

```sh
export RBC_FRONTEND_DIR="$PWD/build/tmp/rbc-inputs/upstream-pyhsb"
export RBC_HISOFT_TAPE="$PWD/build/tmp/rbc-inputs/hisoft48.tap"
python3 -B -m unittest discover \
    -s experiments/hisoft-rbc-2026-10-22/tests \
    -p test_native_raw_five_game_progression.py -v
python3 -B -m unittest discover \
    -s experiments/hisoft-rbc-2026-10-22/tests \
    -p test_native_input_raw_candidate.py -v
```

**The original production RBC INPUT and published Flying Geese replay are
still unresolved.** Native error handling, full ROM editing, independent
BAS/TZX conversion, whole-game paths, and production safety require more
proof before any changed game SSX can be published.

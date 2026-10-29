# Four native games: precise original ROM-error source locations

The linked published SSX files ran in the real ZX-UX loader and Z80 emulator.
Read-only hooks observed original Z80 instructions at the ROM fault sites and
kernel `rom_error` entry. Nothing was rewritten, patched, assembled, or
substituted. The source line mapping comes from the **original HiSoft
line/address table in the loaded image**, checked against the independent
numbered ASCII BASIC source. The traced caller addresses are real machine
return addresses, not guessed line numbers.

| Game | Source line and caller | Original ROM fault | Native error |
| --- | --- | --- | --- |
| Tug of War | `7020`, `DE6C` | String-array `LET` requests `BC=C80C` (51,212 bytes) at ROM `2B7F`; ROM `TEST-ROOM` reaches `1F15` | report 4, `ERR_NR=03` (out of memory) |
| Dogfight | `1040`, `C9C1` | `PRINT AT` receives row `FF`, column `07` at ROM `0A9B` | report B, `ERR_NR=0A` (integer out of range) |
| Exocet | `110`, `C922` | During the source line's scrolling-string output, ROM `PRINT AT` receives row `20`, column `0D` at `0A9B` | report B, `ERR_NR=0A` |
| Dam Busters | `125`, `D0E2` | `PRINT AT` receives row `06`, column `FF` at ROM `0A9B` | report B, `ERR_NR=0A` |

All addresses and register values are hexadecimal. `FF` is 255; `20` is 32.
The ROM permits screen PRINT-AT rows 0–21 and columns 0–31. Every fault goes
through the kernel at `6060` to the `6048` panic handler. Screen ownership is
lost, interrupts are disabled, and there is **no** process exit record or
clean shell return. Passing the diagnostic means the fault was reproduced,
not that the game ran successfully.

## Original source comparison and cause limits

- **Tug of War:** line 7020 assigns a fixed-width string array element after
  `DIM a$(2,6)` and `DIM b$(2,6)` at line 7017. A 51,212-byte destination
  string length is inconsistent with those dimensions. The native compiler
  or selected string runtime is suspect, but the exact corruption site has
  **not** yet been proven. No compiler fix is asserted.
- **Dogfight:** source line 1040 prints at `q(1),q(2)`. The source updates
  `q(1)` by an array step at line 1180, but its negative-row correction at
  line 1118 runs after the next loop's line 1040 display. A `-1` row can
  therefore reach the original PRINT instruction. This is a source-level
  bounds hazard. It cannot be fixed by silently changing the original game.
- **Exocet:** the caller maps to line 110, which prints a scrolling slice of
  `S$`. The ROM receives `AT 32,13`, although the line's explicit `AT 10,0`
  should be valid. Why those control operands were printed is **unresolved**;
  a runtime string/output defect is possible. A line match alone is not a
  proof of the underlying defect.
- **Dam Busters:** line 125 prints the sights at `g,f`. Line 155 changes `f`
  through random movement, and the original source has no unconditional
  clamp after that move. The witnessed `f=-1` gives column `FF`. This is a
  source-level bounds hazard. The game source remains untouched.

The original ROM's `TEST-ROOM` at `1F05` checks `STKEND + BC + 80` against
stack space. The original ROM's `PRINT AT` operand code at `0A9B` rejects
columns greater than 31 and rows greater than 21. These are source-verified
ROM paths, not emulator approximations.

## Repeat

With the unchanged original system tape at `build/out/ZX-UX.tzx` equal to
`dist/zx-ux/tzx/ZX-UX.tzx`, the 48K ROM and kernel symbols:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONWARNINGS=ignore python3 -B -m unittest discover \
  -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_four_rom_fault_origins.py -v
PYTHONDONTWRITEBYTECODE=1 PYTHONWARNINGS=ignore python3 -B -m unittest discover \
  -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_rom_syntax.py -v
```

The four-case diagnostic and six separate ROM syntax cases passed. The
negative diagnostic verifies original BAS/TZX/SSX/ROM hashes before and after
execution and both unmodified 14,000-byte loader admission bounds. The
live-Z80 trace and original compiler line table were used to locate each
failure; a missing or ambiguous table fails the test. No original 120 inputs,
34 SSX files, 26 README files, kernel, ROM or emulator was changed. Overall
complete-outcome coverage remains **23/34**; 11 games remain unfinished.

| Game SSX | Original SHA-256 |
| --- | --- |
| Tug of War | `e12b891fda3b97f0f53ea1c45f8c97caa9115b07f084bfd8d50aa271ff9f3294` |
| Dogfight | `ccea6b421d27023e54590892f2f1350d6f53559ad6f15ba68b59567222cf8a31` |
| Exocet | `ed308cf3e60bc90cf4b17c5bb6ff5b66f05faf3980ec8eeefc0743885f9ff921` |
| Dam Busters | `ba8b31d39abae89ca36498983dba69d21f718172e1ff8b62a3763cf99535dc7c` |

**Decision:** no binary or BASIC change is justified by these observations.
The next bounded source/runtime investigation is the string-array length in
Tug of War and the scrolling-string control operands in Exocet. Preserve
other published games while those two questions are tested.

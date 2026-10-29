# Tug of War: exact cause of the 51,212-byte native allocation

The user's `03-tug-of-war.tzx` has SHA-256
`10c4a2cffbdfec0e6917a4a7ecd311e01a074f61c297b35ca29053d7bbcfdea4`,
identical to the preserved original repository TZX. The numbered ASCII BASIC,
original tape and published SSX were read, not edited. The BASIC initializes
`DIM a$(2,6): DIM b$(2,6)` on line 7017, and assigns six-byte sprite strings
on line 7020. These are valid original string-array dimensions.

## Exact native failure

The published 12,052-byte `03-tug-of-war.ssx` was recreated byte-for-byte
from the original BAS through the checked HiSoft compiler, three independently
located bases, real pre-link assembly, `ras`, and `rld`. Its SHA-256 is
`e12b891fda3b97f0f53ea1c45f8c97caa9115b07f084bfd8d50aa271ff9f3294`.

At line 7017 the generated Z80 stores `0xC80C` in RAM at `0xF1AE`, the live
width of `a$`, and `0xC808` at `0xF1BC`, the live row count. The corresponding
fields for `b$` have the same defect. These are relocated *addresses*; the
required values are respectively `6` and `2`. At line 7020, the original
HiSoft string-array element path returns that bogus width as the requested
length. The real CPU reaches ROM `0x2B7F` (`BC=0xC80C`, decimal 51,212), and
then ROM `TEST-ROOM` / out-of-memory error `ERR_NR=03`. The kernel enters
`rom_error=0x6060` and panic `0x6048`, rather than exiting cleanly. This is
not a long string in the original BASIC, and not a legitimate size request.

**Cause:** `stage/native_string_redim.py`, `StringRedim.st_dim()`, used
`self.ld_hl(width)` and `self.ld_hl(rows)` for numeric constants. The
canonical HiSoft frontend's `Compiler.ld_hl()` calls
`emit_op_reloc('ld hl,nn', addr)`. It is explicitly a *relocating address*
helper. The original frontend uses `emit('ld hl,{}', ent['last'])` to load a
nonrelocatable string width. The native output matched the erroneous frontend
emission exactly at three bases; the assembler and linker did not invent the
error.

## Bounded correction and proof

Only the two mistaken calls in the RBC extension change to
`self.emit('ld hl,{}', width)` and `self.emit('ld hl,{}', rows)`. The backing
string data address still uses relocatable `self.ld_hl(sv['addr']+2)`. No
original game, ROM, emulator, ZX-UX kernel or published SSX was patched.

A fresh checkpoint recovered from the reviewed historical sources plus this
extension compiled the *unchanged* original BAS successfully through the
normal native CLI and real `ras`/`rld` without an optimizer. Byte identity
with the three-base HiSoft reference passed. The new SSX remains **untracked**
under `build/tmp/`; its SHA-256 is
`9c259947f7e117fcc66cca116cecd8e14cec223a5d3bead68e2874675710b4c6`.
It measures file **12,040**, image **10,757**, BSS **111**, stack **384**, total
**11,252** bytes, all within 14,000. The unchanged image size reflects the
same opcodes with two differently classified operands per DIM. The relocation
count decreases from **1,273** to **1,261** across the six DIMs.

The real ZX-UX kernel/Z80 emulator booted that separately compiled SSX and
accepted the original `a` key. RAM then showed widths `6,6` and row counts
`2,2`; all four observed early ROM `0x2B7F` requests were **6 bytes**. In a
1,200-frame post-key run, the game remained live and owned its genuine
6,912-byte screen (including the moving `X` marker); ROM `ERR_NR` stayed `FF`
(no error). This proves the original startup memory fault was corrected, not
that a complete round, win, STOP or shell restoration was tested.

The regression is `tests/test_native_string_redim.py` for nonrelocatable
width/row instructions, and `tests/test_native_tug_string_row_width.py` for
recompilation and real ZX-UX execution. The latter requires a freshly rebuilt
checkpoint in `RBC_TUG_CHECKPOINT_DIR`, a verified frontend in
`RBC_FRONTEND_DIR` and original HiSoft TAP in `RBC_HISOFT_TAPE`; it checks the
checkpoint extension bytes against the checked stage source and leaves all
original game bytes untouched.

The published game binary remains unchanged. Publishing a replacement game
SSX would be a separate release decision requiring the original 60-game
BAS/TZX pairing and applicable native safety gates; this source fix does not
claim that release or a verified full Tug of War round.

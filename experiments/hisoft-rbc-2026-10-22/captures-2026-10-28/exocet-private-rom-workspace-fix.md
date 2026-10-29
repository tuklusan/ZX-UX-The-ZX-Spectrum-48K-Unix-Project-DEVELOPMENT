# Exocet: source-witnessed private ROM string workspace

The original Exocet BAS and TZX decode to the same BASIC lines; the explicit
`PRINT AT 10,0` is valid. In the formerly published SSX, Spectrum ROM string
construction uses RAM `$5DCD` as a work byte. ZX-UX independently owns that
byte as `tapq` and decrements it in the interrupt handler. A string that began
with a space (`$20`) can therefore acquire `$16`, the ROM's `PRINT AT` control
byte. The following bytes yield the observed illegal `(32,13)` coordinate.
This is the independently reproduced cause, not an invalid original BASIC
literal or a TZX conversion fault.

The native emitter now supports a **private, loader-budgeted 1024-byte** ROM
string workspace. The process entry saves ROM system variables `WORKSP`
(`$5C61`), `STKBOT` (`$5C63`) and `STKEND` (`$5C65`), redirects them into
private BSS before HiSoft's original source-verified program runs, and restores
them when it returns through the wrapper exit. All of these operations are
symbolic Z80 source assembled by `ras` and linked by `rld`. No ROM, kernel,
original BASIC/TZX, image bytes, or published game SSX were patched.

This exception is enabled only when the independently rebuilt HiSoft frontend
reports the exact archived original Exocet BAS SHA-256
`85af9782454aa018786dd9feeca03b5a10785ca1ff59d1f08beb2d2e74515e0a`
and matches the original source statements. Line 1235 seeds `Q$` and `S$`
with 32 spaces; lines 1240-1260 concatenate 100 six-character `G$` entries;
line 1270 appends the 32-character `Q$`. This proves a maximum 664-character
`S$` capacity rather than the previous 255. No unrelated large string can
opt in. Any changed source loses that proof. The ordinary three-base HiSoft
pre-link source, original relocations, and baseline native/HiSoft byte
comparison remain mandatory before the extra wrapper is assembled. The
compiler still enforces the unchanged 14,000-byte loader admission and the
unchanged `RBC E_PRINT_AT_RANGE` check.

A locally rebuilt native Exocet SSX (untracked, not a published game binary)
was compiled from its unchanged BAS through `ras`/`rld`. Its native file was
8,404 bytes, image 7,505, BSS 1,920, stack 384, and total 9,809 bytes. A real
ZX-UX loader and Z80 emulator ran it through the former failure window for
1,400 frames after starting the game. It retained screen ownership, and the
read-only hooks observed neither a ROM error nor illegal `PRINT AT`. The real
kernel's `tapq` byte was not overwritten by a ROM string copy. An independent
minimal native fixture checked that the saved ROM system pointers and shell
screen ownership are restored on normal process completion.

The real Exocet run did **not** demonstrate a complete game, STOP, or replay.
Error unwinding, concurrent process isolation, and all input sequences remain
unproven. The published original Exocet SSX remains byte-for-byte unchanged.

Dogfight and Dam Busters are **not** fixed by this change. Dogfight's original
line 1180 may move `q(1)` below zero after the correction at line 1118 and the
line 1040 condition tests only the upper bound. Dam Busters' original line
155 may decrement `f` below zero after the guard at line 122. Original BAS
and independent TZX agree in both games. A separately proven compiler defect
versus BASIC interpreter timing/random behavior has not been established.
Silently wrapping, clamping, or weakening range checks would hide these
source-permitted paths. These two outcomes therefore remain open, rather than
being claimed as fixed. The three original sources and their published SSXs
remain preserved.

Reproduce from repository root after recovering the checked compiler into
`build/tmp/rbc-current-exocet-candidate/rbc`, and the original HiSoft frontend,
tape and ROM into the test's existing `build/tmp` paths:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONWARNINGS=ignore python3 -B -m unittest discover \
 -s experiments/hisoft-rbc-2026-10-22/tests \
 -p test_exocet_private_rom_workspace.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -B build/tools/zx-tzx2bas.py \
 --corpus src/bonus/60-programs --verify-corpus
```

A skipped integration test (missing external HiSoft frontend or recovered
compiler) is not a game validation pass. No gameplay screenshot was captured
for this partial Exocet run.

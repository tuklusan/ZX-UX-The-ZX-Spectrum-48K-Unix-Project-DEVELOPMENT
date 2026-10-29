# RBC PRINT AT constant-range check and Tug of War memory result

The strict, reproducibly rebuilt native RBC source tokenizer now rejects a
**provably out-of-range constant** `PRINT AT` row or column before compilation.
The new diagnostic has the existing RBC error form and original BASIC line:

```
RBC E_PRINT_AT_RANGE: Line 10: PRINT AT row 32 outside 0..21 (Spectrum 48K ROM screen)
RBC E_PRINT_AT_RANGE: Line 10: PRINT AT column 255 outside 0..31 (Spectrum 48K ROM screen)
```

The 48K screen has 24 physical text rows; the ROM `PRINT AT` command is
restricted to **rows 0–21** and **columns 0–31**. Thus `AT 32,13`, `AT
22,0`, and `AT 6,255` are invalid. Constant arithmetic with a provable
integer value is checked. The check reads original token bytes and ignores
quoted text, REM, DATA and hidden number bytes. Valid boundaries and
unresolved dynamic expressions are unchanged. No original BASIC was edited;
the compiled image and original ROM are not patched.

**Scope:** this is a compile-time check for *proven constant* coordinates,
not a fabricated proof of runtime bounds for variables, arrays, scrolling
strings, fractional values, or computed flow. The ROM still rejects invalid
dynamic coordinates at execution. The published game SSX files are unchanged.
Existing native panics in Dogfight and Dam Busters come from dynamic movement
values. Exocet's observed `AT 32,13` came from rendering a runtime string
slice at source line 110, **not** the line's explicit `AT 10,0`; its control
byte origin remains unresolved. This static check cannot certify those games.

## Tug of War: memory failure is not a provable source-constant overflow

Original `03-tug-of-war.bas` line 7017 uses `DIM a$(2,6)` and
`DIM b$(2,6)`. Line 7020 then assigns elements using six visible `{xx}`
character escapes each, matching that fixed width. A local compile-time
string-length check cannot derive the 51,212-byte allocation later witnessed
at `LET a$(1)` from these bounded source values. The real native run reaches
ROM `TEST-ROOM`, with `BC=C80C`, reports out of memory, and enters the kernel
panic loop. The selected string-array compiler/runtime remains suspect;
the exact corruption site is **not proven**. The recorded runtime failure
cannot be attributed to a known static bound or a verified clean return.
The runtime failure is retained as a documented negative result. Do not change the game, patch
its SSX, or weaken the ROM/loader protections to hide it.

## Checks

Run from the repo root:

```
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests -p test_print_at_bounds.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests -p test_rom_syntax.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests -p test_native_four_rom_fault_origins.py -v
```

The standalone source-tokenizer regression also retokenizes all 60 untouched
BAS originals and checks that no existing game is newly rejected. This is not
an independent 120-input native compile/execute run, nor proof that a game
round or shell restoration completed.

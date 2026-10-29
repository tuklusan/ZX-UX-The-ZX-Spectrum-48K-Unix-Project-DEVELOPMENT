# Original Dogfight, Exocet, and Dam Busters: PRINT AT lineage

The source programs remain untouched. We independently extracted each original
BASIC program from the saved TZX using `build/tools/zx-tzx2bas.py`. Every decoded
listing line agrees with its archived numbered BAS line after removing only the
left listing margin: Dogfight **126/126**, Exocet **94/94**, Dam Busters **73/73**.
The corpus-wide converter comparison also returned **60/60 verified**. Thus no
altered `AT` operands, source expression, or quoted string were introduced by
TZX extraction or ASCII conversion in these three cases. The compiler's
existing `RBC E_PRINT_AT_RANGE` check is unchanged; these are runtime values.

## Original native coordinates, reproduced without source changes

| Original TZX | Source statement | Live ROM `PRINT AT` path | Interpretation |
| --- | --- | --- | --- |
| `43-dogfight` | `1040 IF q(1)<21 THEN PRINT ...;AT q(1),q(2)` | `(0,8)` followed by `(255,7)` | A negative row from `1180 LET q(1)=q(1)+e(aa)` can survive to the next loop's `1040`. The negative correction at `1118` executes **before** `1180`, not after it. |
| `47-exocet` | `110 ... AT 10,0;S$(x TO x+31)` | A string's embedded `0x16` later produces `(32,13)` | The written coordinate is valid; a different, kernel-overlapped string byte is being interpreted as a new `AT` command. |
| `28-dam-busters` | `125 PRINT OVER 1;AT g,f;...` | `(6,0)` followed by `(6,255)` | The wind at `155` can subtract 1 from `f` after the guarded manual movement at `122`. There is no subsequent lower-bound clamp. |

The Dogfight and Dam Busters coordinate sequences are authentic observations
from the unchanged published SSX binaries in the ZX-UX loader/Z80 emulator.
The original source permits these paths, but this **does not establish** that
an actual Spectrum BASIC interpreter will follow the same RND/keyboard sequence,
or that there is no separate compiler arithmetic or timing defect. A ROM
`0x0A9B` error is not a completed round or normal shell return.

## Exocet: exact byte path

The original `47-exocet.tzx` has `AT 10,0` at line 110. Its `S$` is built by
lines `1235` to `1270`, with `LET S$=S$+G$(INT (RND*10)+1)` at **1250**.
The native image's HiSoft line/address table maps `0xCFA6` to line **1250**
and `0xC91F` to line **110**.

Read-only machine-bus observations:

1. ROM string-copy instruction `0x35B7` (`LDIR`) writes `0x20` to **`0x5DCD`**.
2. ZX-UX kernel symbol `tapq` occupies **`0x5DCD`**. Its 50 Hz ISR executes
   `DEC (HL)` at **`0x60E8`**, turning the copied `0x20` into `0x1F`.
3. During line **1250**, native HiSoft copy instruction **`0xDB1C`** (`LDIR`)
   reads `0x5DCD` and writes it into the string buffer at **`0xE5DF`**.
   Repeated observations show `0x20`, `0x1F`, ... through **`0x16`**.
4. During line **110**, ROM string printing at **`0x2043`** outputs the
   `0x16` stored at `0xE5DF`. Spectrum interprets that value as a new `AT`
   control code. Its following operand bytes are `0x20,0x0D`, producing the
   invalid **row 32, column 13** and ROM error B (`ERR_NR=0x0A`).

This is an observed RAM ownership conflict between the HiSoft string work
area and the ZX-UX kernel's tape timer. It is **not** a TZX-to-ASCII filter
error, and not caused by the explicit `AT 10,0`. As a separate bounded
hypothesis, we reserved **664** bytes for `S$` instead of the compiler's
**255**; the three-base `ras/rld` build fitted the original 14,000-byte limit,
but native execution still reached ROM error B. Buffer size alone is therefore
**not** a demonstrated fix. The altered diagnostic SSX was untracked and is
not a published game file. We did not patch the game, ROM, kernel, emulator,
loader, or published SSX.

## Reproduction

From repository root with the authentic ZX-UX system tape, ROM, font and
published original SSX files:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONWARNINGS=ignore python3 -B -m unittest discover \
  -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_print_at_tzx_origins.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -B build/tools/zx-tzx2bas.py \
  --corpus src/bonus/60-programs --verify-corpus
```

The checked two-case test passed: all original lines from the three independent
TZX files match their BAS counterparts, and the live Exocet bus/ROM lineage
is reproduced without altering instruction execution. The earlier checked
`test_native_four_rom_fault_origins.py` records the three ROM error locations;
the longer Dogfight/Dam Busters coordinate progression was separately observed,
but a new combined long regression exceeded its time limit and is **not**
claimed as a pass. No resolved gameplay or shell restoration is claimed.

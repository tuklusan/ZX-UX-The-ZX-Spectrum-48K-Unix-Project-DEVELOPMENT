# runix SDK — C Compiler, Virtual Machine and Kernel C Support

**Revision 1 — design specification, companion to SPEC-ELASTIC-R1**

This document covers the C toolchain for runix and what the kernel adds to support it:
- the C compiler
- the linker, the tape writer and the virtual machine
- the runtime library
- the kernel's C-support extensions

It rests on measurements of the C48 SDK corpus (§2). Where it touches SPEC-ELASTIC-R1, the elastic memory model and the SS formats apply unchanged.

## 1. Decisions

| # | Decision |
|---|---|
| S1 | The compiler is a standalone **Python** tool on the host. There is no native compiler on runix. |
| S2 | The source language is **C48 as defined by the C48 Language Specification Rev 0.11** (ZX-UX repository). The **ZX-UX C48 SDK** compiler is the behaviour reference: same diagnostics policy, same program results. runix's implementation is independent. |
| S3 | The SDK lives in the runix repository (`sdk/`), next to the kernel and its tools. |
| S4 | The compiler's output is consumed by the **runix VM** on the host and is also written as a **runix executable on tape** (SSX1 in SST1). |
| S5 | Size strategy, in order: **(1)** a size-optimising native Z80 code generator; **(2)** a compact **bytecode mode** (SSB1, §6) for programs native code can't fit (`chess`, `write48`, the large apps); **(3)** in reserve, moving resident commands to tape to enlarge the arena (SPEC-ELASTIC-R1 §13). |
| S6 | Acceptance: every C program in the SDK corpus compiles and runs, in the VM and on runix from tape, with results matching the SDK reference. Exempt: `ailmzx48`. Best effort: `queens8` and `hanoi`. |

## 2. Measured starting point

The SDK's own native backend (`c48b2tap`) can't lower any corpus program as shipped:
- its runtime has no `print_at`, `beep`, `draw` or UDG calls
- it rejects non-constant aggregate initializers

With trivial stubs for the missing calls, it lowered 47 programs. Native image + bss, at SDK backend code density (2.2–3.5 bytes of Z80 per byte of C source):

| Native size | Count | Programs |
|---|---|---|
| ≤ 12.5 KB | 20 | examples, security fixtures, `tune`, `arith`, `wump`, `advent`, `rogue`, `spriteanim`, `plasma`, `mandel` |
| 12.5–16 KB | 20 | most graphics demos, `snake`, `fish`, `trek`, `gp82` |
| > 16 KB | 7 | `bgammon` 17.2, `cribbage` 18.0, `sheet48` 19.6, `dizzy4k` 20.1, `queens8` 20.7, `wire3d` 21.7, `hanoi` 24.9 |
| not lowered | 11 | `write48` (> 32 KB), `chess` (est. ~70 KB at this density), `goblet`, `morph3d`, `argv`, `colors`, `fortune`, `hangman`, `maze`, `quiz` (initializers), `seckern` (rejected by design) |

The runix 2.x budget for one program is about 14 KB (SPEC-ELASTIC-R1 §3.5).

**Targets that follow:**
- the native generator must be at least **30 % denser** than the SDK backend, so that the borderline group fits
- the bytecode mode must reach about **2.5×** the density of SDK native code, so that `chess` and `write48` fit

## 3. Toolchain architecture

    C48 source
      -> rcc front end   preprocess, lex, parse, check   (C48 Rev 0.11)
      -> IR              typed, per function
      -> backend         native Z80   or   SSB1 bytecode   (per program; §6)
      -> SSO1 objects
      -> rld             links with the runtime library (SSA1), keeping only what is referenced
      -> SSX1 executable
      -> rtap            SST1 cassette record(s) as .tap/.tzx
      -> rvm             runs the SSX1 on the host (§7)

| Tool | Role |
|---|---|
| `rcc` | C48 compiler (front end, IR, both backends) |
| `ras` | Z80 assembler producing SSO1 (runtime library, hand-written routines) |
| `rld` | linker: SSO1/SSA1 → SSX1 |
| `rtap` | SSX1 and data files → SST1 tapes |
| `rvm` | the runix VM |

Tool names are provisional.

**Choosing a backend:** `rcc` builds native by default. If the linked native image plus bss, heap and stack exceeds the budget given by `--max`, or the user asks with `--bytecode`, it rebuilds in bytecode mode. A later revision may mix the two per function: native for hot loops, bytecode elsewhere.

## 4. Runtime library

The runtime is written in C48 and in `ras` assembler, delivered as SSA1 archives, and linked per program. Only referenced members are included.

| Area | Implementation |
|---|---|
| strings, memory | Z80 routines (block instructions) |
| `malloc` / `free` | first-fit heap in the program's own block, grown with `break` |
| `putchar`, `puts`, `print_at`, `cls` | tty writes using AT and the colour control codes (§5.1) |
| `getchar` | raw tty mode (single keys, no echo), as the C48 spec defines |
| `ink`, `paper`, `bright`, `flash`, `inverse`, `over` | colour control codes (§5.1) |
| `border` | OUT to port FEh, and the border copy in BORDCR |
| `plot`, `point`, `draw`, `circle` | Z80 code writing the display file directly; no ROM drawing routines, which need BASIC system variables |
| UDGs (`udg_define`, `udg_get`, `udg_draw`, `udg_draw_2x2`, `udg_clear`) | a 21-entry UDG bank in the program's memory; drawing writes the display file |
| `ticks`, `yield`, `sleep`, `exit`, arguments | system calls (§5.3; `rele`, `sleep`, `exit`; v1 argument layout) |
| float arithmetic and `sin` … `fabs` | conversions and comparisons in Z80; arithmetic and functions through the kernel's float service (§5.4) |
| `beep` | pitch and duration converted with the float service, then `sys beep` (§5.5) |
| `open`, `close`, `read`, `seek` | runix file system calls (no corpus program uses them) |

## 5. Kernel C-support extensions

These five extensions are part of the runix kernel and are emulated by `rvm` with identical behaviour. Estimated kernel cost is about 300 bytes. New system call numbers follow 37 `zxpack`.

### 5.1 Console colour codes (no new call)

`kputc` accepts the Spectrum control codes, each followed by one parameter byte, alongside AT (16h) and INVERSE (14h):

| Code | Meaning |
|---|---|
| 10h n | INK n (0–7) |
| 11h n | PAPER n |
| 12h n | FLASH 0/1 |
| 13h n | BRIGHT 0/1 |
| 15h n | OVER 0/1 (XOR glyphs into the display) |

Printed characters set the attribute byte of their 8×8 cell. Two 4×8 characters share one attribute cell, so the later one's colours win. This is inherent to 64-column text on the Spectrum and is documented, not hidden. FF (`cls`) clears using the current colours.

### 5.2 `sys screen` (39) — full-screen ownership

| Call | Effect |
|---|---|
| `HL = 1` | claim the screen for the calling process: status line and cursor blink suspended; text addressing extends to 24 rows (AT row 23 valid) |
| `HL = 0` | release: clear the screen and restore the status line |

- Only one process can own the screen; another claim fails with `EBUSY`. Ownership is released automatically when the owner exits or `exec`s.
- Other processes' tty output still appears; the screen is shared like a terminal.
- The runtime claims the screen at program start, so graphics and full-screen text behave as in the SDK.

### 5.3 `sys ticks` (38)

Returns the 50 Hz frame counter: low 16 bits in HL, high 16 bits in DE. The counter is 32-bit, incremented by the clock interrupt, never reset, and wraps.

### 5.4 `sys fp` (40) — five-byte float service

`HL` points to a 16-byte request block:

    +0   u8  op
    +1   u8  reserved (0)
    +2   x   5-byte float (first operand)
    +7   y   5-byte float (second operand; binary operations only)
    +12  4 bytes reserved
    result: written over x

| op | Operation | op | Operation |
|---|---|---|---|
| 1 | x + y | 10 | ln x |
| 2 | x − y | 11 | sin x |
| 3 | x × y | 12 | cos x |
| 4 | x ÷ y | 13 | tan x |
| 5 | x ^ y | 14 | asin x |
| 6 | \|x\| | 15 | acos x |
| 7 | −x | 16 | atan x |
| 8 | int x (truncate) | 17 | sqrt x |
| 9 | exp x | | |

- **Errors:** carry set; A = `ERANGE` (ROM "Number too big") or `EDOM` (invalid argument); x unchanged.
- **Implementation:** the kernel runs the ROM calculator (RST 28h) on its own stack. It first points the `MEM` system variable at a private 30-byte calculator memory and sets `STKBOT`/`STKEND` to a private calculator stack. The kernel's data in MEMBOT is never touched, and the ROM's room check passes.
- ROM errors are caught through the kernel's `ERR_SP` handler and returned as errors instead of panics.
- Results are those of the Spectrum ROM, as the C48 specification requires.

### 5.5 `sys beep` (41)

`HL` = pitch period and `DE` = duration count, as ROM BEEPER takes them. The runtime converts C48's `beep(duration, pitch)` with the float service.

The kernel runs BEEPER, during which interrupts are off, then advances the frame counter and clock by the elapsed time computed from `HL` and `DE`. Other processes don't run during a beep, as with tape operations.

## 6. SSB1 — bytecode mode

SSB1 is a compact stack-machine instruction set for C48. A program in bytecode mode is still an ordinary **SSX1** executable:
- its image holds the SSB1 **interpreter** (a Z80 runtime member of 2–3 KB)
- plus the program's bytecode and data
- the kernel and the SSX1 format are unchanged

**Instruction set requirements:**
- one-byte opcodes, with short forms for common operands: small constants, frame slots 0–15, near jumps
- 16-bit integer and pointer arithmetic, `char` loads and stores, calls and returns with frames
- calls to native runtime routines by index, so library code is shared with native mode
- float operations through the same runtime routines as native mode

**Targets:**
- density about 2.5× better than SDK native code
- speed within 10× of native code
- graphics primitives stay native, so graphics-heavy programs remain usable

The opcode table is defined in revision 2 of this document, once the IR exists and real programs can be measured.

## 7. The runix VM (`rvm`)

`rvm` runs **the same SSX1 file that goes to tape**, on an emulated Z80 (the C Z80 core with T-state timing that the runix test harness already uses). The runix kernel interface is emulated in Python. What is tested is what ships.

**Emulated faithfully:**
- the system call interface (call 6003h), including the extensions in §5
- the 64×23 console with status line, and the full-screen mode of §5.2, drawn into a real 6,912-byte display file with the runix 4×8 font
- the attribute rules of §5.1
- the 50 Hz clock: `ticks` and `sleep` in frames, computed from emulated T-states
- **multitasking:** up to 4 processes with preemptive time slices of 4 frames, as in runix, with `yield`, `sleep` and `wait`
- floats with the ROM's exact results (the VM runs the real ROM calculator code, the same way the kernel will)
- `beep` recorded as (period, duration) events
- keyboard input from a script

**Outputs:**
- the text transcript
- screen dumps (`.scr`) at chosen frames
- the beep log
- exit status

These are compared with the SDK reference runner (`c48run`).

## 8. Acceptance

For each corpus program (except `ailmzx48`):

1. `rcc` compiles it with no errors. Native mode is used unless it doesn't fit, in which case bytecode mode.
2. In `rvm` it produces the same transcript and screen dumps at the same frames as `c48run`, given the same scripted input and the same frame budget as the SDK's verification gates.
3. It loads from a runix tape and runs on runix in the emulated Spectrum (the existing `zxrun` harness), reaching its first screen and responding to scripted input.

Size reports are published per program: native size, bytecode size, and the mode used. `queens8` and `hanoi` are attempted; if they don't fit, the report says by how much.

## 9. Phases

These replace phases 4–5 of SPEC-ELASTIC-R1.

| Phase | Content | Gate |
|---|---|---|
| K | Kernel extensions §5.1–§5.5 (can follow phase 1 of SPEC-ELASTIC-R1) | regression suite passes; tests for each call; float results match the ROM bit for bit |
| 4a | `rcc` front end and IR; `rvm` with the kernel interface; runtime library in C48 and `ras`; a temporary IR interpreter in `rvm` until the backends exist | the corpus parses and type-checks like the SDK; examples run in `rvm` |
| 4b | Size-optimising native backend, `rld`, `rtap` | at least 30 % denser than the SDK backend on the 47 measured programs; acceptance §8 for every program that fits |
| 4c | SSB1 bytecode backend and interpreter | `chess`, `write48` and the large apps pass §8 |
| 6 | Measure and tune (SPEC-ELASTIC-R1) | size reports for the whole corpus |

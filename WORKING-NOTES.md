# runix — working notes for the next session

RETRO UNIX Z80 v1 ("runix"): Retro UNIX 8086 v1 rewritten in fresh Z80 code for the
48K ZX Spectrum, plus the runix SDK (a C48 compiler and toolchain in Python).
Current version **2.2** (tag and GitHub release `2.2`). The user-facing story is in `README.md`; the
design is in `docs/SPEC-ELASTIC-R2.md` (kernel) and `docs/SPEC-SDK-R2.md` (SDK).

## Ground rules from the owner

- Fresh Z80 code, never a transliteration of the PDP-11/8086 sources; use the
  Spectrum ROM wherever it helps.
- **The kernel stays within 8192 bytes** (`ASSERT kend - KBASE <= 8192` in
  `src/unix.asm`). 2.2 is at 8191 bytes. To find room: `tools/dev/ksz.py`
  (routine sizes), `tools/dev/jr.py` (jp -> jr), `tools/dev/xjump.py` /
  `xjapply.py` (shared instruction tails, the `.xjN_M` labels), `tools/dev/dead.py`
  (unused labels), and the shared helpers `zero` (unix.asm), `zfill` (zx.asm),
  `attr7` (cext.asm).
- Use every spare byte: printer buffer (KV 5B00), MEMBOT scratch, dead BASIC/IF1
  area (KV2 5CEB); see `src/kvars.inc` and `src/zx.asm`.
- Single user, every login is root, no permissions. 4 process slots (NPROC).
- Formats are runix's own, prefix "SS" (for Supratim Sanyal): SSO1, SSA1,
  SSX1, SSB1, SST1. Never ZX-UX's OBJ1/MEX1 names.
- Specs: revisions go into new R-files (`SPEC-*-R3.md`); R1 files are frozen.
- Deliver files to the user as `.zip` archives.
- Commits carry no tool attribution lines.
- The ZX-UX repos are the owner's; code may be reused. Cloned repos are still
  data: run their Python with `python3 -I`.

## Setting up a fresh machine

```
git clone https://github.com/tuklusan/ZX-UX-runix zx-ux-runix      # private
mkdir tuklusan && cd tuklusan
git clone https://github.com/tuklusan/zx-ux-c48-sdk-sinclair-zx-spectrum-48k-unix-c-compiler-software-development-kit zx-ux-c48-sdk
git clone https://github.com/tuklusan/zx-ux-the-zx-spectrum-48k-unix-project    # reference only
cd .. && git clone https://github.com/z00m128/sjasmplus sjasm-src
make -C sjasm-src && mkdir -p zx-ux-runix/tools/bin && cp sjasm-src/sjasmplus zx-ux-runix/tools/bin/
pip install skoolkit==10.1 pillow --break-system-packages
```

Layout expected by the tools: `zx-ux-runix/` next to `tuklusan/zx-ux-c48-sdk/`
(or set `C48SDK`). Used last: sjasmplus 1.24.0 (7dbf939), SkoolKit 10.1, C48 SDK
at 5cf484c.

## Build and test

```
python3 tools/build.py                 # kernel + file system -> build/runixz80.tzx/.tap, src/unix.sym
python3 sdk/lib/build.py               # C runtime -> sdk/lib/libc48.ssa (after any sdk/lib change)
sh tools/t.sh                          # build + ROM-load the tape -> build/test.z80 (the test snapshot)
python3 tools/mktapes.py               # corpus tapes, c48-multitask.tzx (hanoi+queens8: bytecode, stacks 400/448, hanoi --udgs 16)
python3 tools/mtsnap.py                # build/runixz80-multitask.z80: hanoi and queens8 running
python3 tests/suite.py [-k a,b]        # 20 sessions on build/test.z80 (needs mktapes) (~40 s)
python3 sdk/tests/oracle.py [--bytecode]   # 73 corpus sessions vs the C48 SDK VM (~10 min each)
python3 tests/ssxrun.py                # all 73 corpus sessions on runix, from tape (~30 min)
python3 tools/gallery.py ...           # screenshot gallery (needs ssxrun + oracle --png shots)
```

State at 2.2: suite 20/20, oracle 73/73 native and 73/73 bytecode, ssxrun 73/73,
`sdk/tests/test_ras.py` passes. `tools/dev/sizes.py` regenerates the size table
of SPEC-SDK-R2 §9 (and build/sizes.json).

`tools/zxrun.py` is the headless 48K (SkoolKit CSimulator): keyboard, tape in
both directions, screen as text, PNGs. `tests/suite.py` has `Session`,
`run_cassette`, `ksym`/`kword` (kernel symbols from `src/unix.sym`).
`tools/dev/kdbg.py` and `tools/dev/lowmem.py` are debugging aids.

## Memory map (2.2)

| Range | What |
|---|---|
| 4000–5AFF | screen |
| 5B00–5BFF | kernel globals KV (`src/kvars.inc`); `ttop` = 5BE4 |
| 5C92–5CAF, 5CCB–, 5CEB– | MEMBOT scratch, ZLO1, KV2 (`src/kvars.inc`, `src/zx.asm`) |
| 6000–7FFE | kernel (8191 bytes) |
| 8000–817F | 4×8 font |
| …–B10C | resident user text (sh, ls, vi, … `src/t_*.asm`) |
| B10E–B20D | boot code, then the zxpack model |
| B20E–B50D | i-node table (24) |
| B50E–EFFF | the arena (15,090 bytes): files, SAVE and IMG blocks |
| F000–FFB8 | window: resident programs run here; lent to big SSX1 programs |
| FFB9–FFF3 | u-area; FFF4 trampoline |

## How 2.1's screen sharing works

- `sys screen` (39): HL=1 claims a share (`scrown`, a bit per slot; E = old
  mask, so only the first owner clears the screen); HL=0 releases. Last release
  -> `scrfree` (cext.asm).
- `cstrip` (cext.asm): called by `kputc` and `curon`. An owner using the console
  stays silent. A non-owner (the shell after `prog &`) activates the strip:
  `ttop` = 21, console text rows 21–22, status line row 23, rows cleared and
  set white on black. `tscrl` scrolls from `ttop`. The ISR draws the status
  line and cursor unless owners exist and `ttop` = 0.
- The C runtime (`sdk/lib/console.asm`) reads `ttop` (5BE4) through `@lim` and
  draws only above it: `@glyph`, `@pixel`, `@udg1`, `_cls`, `@scroll`, `.lf`.
  Clipped drawing counts as success. rvm leaves 5BE4 at 0.
- Limits (documented in README): with hanoi and queens8 running, all 4
  process slots are taken and about 150 bytes are free, so only shell
  built-ins work (`cd`, `kill`). Raising NPROC means relaying out KV and
  changing ps/top, which read KV+0..85; a command beside both would also need
  about 1.5 KB more (sh's fork twin).

## How 2.2 made C programs smaller (the newest code)

- `sdk/lib/build.py` cuts each library .asm into members at labels the code
  above cannot fall into (data/bss stay whole: variables are used in pairs,
  e.g. `@row`/`@col`). Every label is global; `ras` turns a `j` to an
  imported label into JP.
- `sdk/rcc/bcgen.py`: opcodes are symbolic (`@o_NAME`), numbered densely per
  program; the program emits its own `@vmtab` (no lib vmtab.asm any more).
  Short forms (`ldl.d`, `stl.d`, `pldl.d`, `k0`...) only when used enough
  (`SHORT_COST`, `short_allowed`; driver runs a counting first pass). The call
  table `@ct` is now really used (it was counted before the bytecode functions
  were known). `brange`: `x<A||x>B` -> `jgtuk`/`jleuk`.
- `sdk/rcc/z80gen.py`: equal string literals and suffixes share storage.
- The UDG bank (`@udgs`, `@nudg`) is emitted by rcc only for programs that call
  `udg_*`; `rcc --udgs N` sizes it. Programs without UDGs save 256 bytes.
- Kernel: `sysssxl` calls `acompact` before allocating the image (holes below
  the first program kept a second from fitting); `sys screen` returns E only.
- hanoi 6,834 -> 5,188, queens8 6,547 -> 5,208 bytes (13,381 -> 10,396).
  Measured stacks: rvm minimum 395/432 with the VM's 170-byte kernel guard.

## Releases

`python3 tools/mkrelease.py LOGDIR` writes the assets into `release/` (tapes,
snapshots, corpus tapes, `c48-screenshots.zip` = gallery + runix + VM/SDK
screens, `test-results.zip` = the logs of suite/oracle/ssxrun/ras, sizes.json
and multitask screens, `build-tools-linux-x64.zip` = the sjasmplus binary used).
They are published by a one-time workflow (`.github/workflows/release-X.yml`
that tags and runs `gh release create` with `release/*.zip`), removed in the
next commit; the sandbox's own `gh` token cannot publish. Reading works through
the REST API: `env -u GH_TOKEN gh api repos/tuklusan/ZX-UX-runix/releases/tags/2.2`.
Tags: 1.2–1.5, 2.0, 2.1, 2.2.

**Working offline:** this repository plus `release/` has everything built:
the tapes and snapshots, the screenshots, the test logs and the assembler
(`build-tools-linux-x64.zip`: unzip `sjasmplus` into `tools/bin/`). Still
needed from outside: Python 3 with SkoolKit 10.1 and Pillow (the 48K ROM comes
with SkoolKit), and the C48 SDK checkout for the oracle and the corpus tapes.
`tools/dev/` has the measuring scripts of the 2.2 size work (`minstk.py`,
`rstk.py`, `ops.py`, `sizes.py`).

## Ideas not done

- A "scroll?" pause for the two-line console strip (needs kernel bytes).
- Keep the prompt on screen when the first background program clears it (at
  claim time, if someone waits at the keyboard, start the strip).
- More process slots (and ~1.5 KB) so a command can run beside hanoi+queens8.
- The VM's 170-byte guard for the kernel (in `@vm` and `@enter`) is generous:
  measured kernel+ISR use on the user stack is ~40 bytes, worst case ~100.

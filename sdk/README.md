# runix SDK

The C compiler, toolchain and virtual machine for runix 2.x programs. The C programs run from cassette on a 48K ZX Spectrum running runix. Everything runs on the host in Python 3 with SkoolKit (for the Z80 core and the 48K ROM). The design is in `../docs/SPEC-SDK-R2.md`.

The source language is **C48** (C48 Language Specification Rev 0.11, ZX-UX project). The ZX-UX C48 SDK is the behaviour reference: every program of its corpus gives the same screens here as in its reference VM.

## Quick start

```
python3 sdk/lib/build.py                       # build the runtime archive lib/libc48.ssa
sdk/bin/rcc hello.c -o hello.ssx               # compile and link (native, or bytecode if big)
sdk/bin/rvm hello.ssx --png hello.png --text   # run it on the host
sdk/bin/rtap -o hello.tzx hello.ssx            # its cassette record
```

To run it on runix:
1. Boot `build/runixz80.tzx` and log in.
2. Play `hello.tzx` and type `/dev/cassette/hello`.

Arguments follow the name as usual. The kernel finds the program on the tape (passing over anything else) and loads, relocates and starts it. While it runs it owns the screen; when it ends, the shell carries on below its picture.

## Tools

| Tool | Does |
|---|---|
| `bin/rcc` | C48 → SSX1. `-S` assembly, `-c` object, `--bytecode` / `--native`, `--max BYTES` (default 14000: above it, bytecode), `--stack N`, `--udgs N` (a UDG bank of N slots instead of 32) |
| `bin/ras` | Z80 assembler → SSO1 objects |
| `bin/rld` | linker: SSO1 objects and SSA1 archives → SSX1; `--archive` builds an archive |
| `bin/rtap` | SSX1 → cassette records (`.tzx`/`.tap`); `--after runix.tzx` appends them to a copy of the system tape |
| `bin/rvm` | runs an SSX1 program: `--keys`, `--frames`, `--ticks`, `--root DIR` (files), `--png`, `--scr`, `--text` |

## Library

`#include <c48.h>` (`include/c48.h`) declares what the runtime provides:
- **console:** 64 × 24 text in the 4 × 8 font, colours, `plot`/`point`/`draw`/`circle`, 21 UDGs;
- **keyboard:** `getchar` gives raw keys;
- **time:** `ticks`/`yield`/`sleep`;
- **strings and memory**, and `malloc`/`free`;
- **five-byte floats** and `sin` … `pow`, computed by the Spectrum ROM, bit-exact;
- **sound:** `beep`;
- **files:** `open`/`close`/`read`/`seek`;
- **process:** `exit`, `getpid`.

## Tests

```
python3 sdk/tests/oracle.py [--bytecode] [--only a,b] [--png DIR]   # rcc + rvm against the C48 SDK reference VM
python3 sdk/tests/test_ras.py                                       # ras against sjasmplus
python3 tests/ssxrun.py [--only a,b]                                # every program on runix, from tape
python3 tools/mktapes.py                                            # corpus tapes in build/
```

The oracle reads the C48 SDK from `../tuklusan/zx-ux-c48-sdk` (or `$C48SDK`).

## Licence of the corpus

The C48 corpus programs and the 4 × 8 font come from the ZX-UX C48 SDK, © SANYALnet Labs, under the SANYALnet Labs Non-Commercial License. The compiled programs and tapes built from them carry that licence.

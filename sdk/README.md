# ZX-UX C48 tools

These tools build and run small C48 programs for the ZX Spectrum 48K.
The compiler runs on your host computer, not inside ZX-UX.
The output is an SSX1 program that can run in the VM or load from tape.

## Make a program

First build the C48 runtime:

```sh
python3 sdk/lib/build.py
```

Then compile a C file and make a cassette record:

```sh
sdk/bin/rcc hello.c -o hello.ssx
sdk/bin/rtap -o hello.tzx hello.ssx
```

Load `build/ZX-UX.tzx` and log in.
Type `/dev/cassette/hello` in ZX-UX, then play `hello.tzx`.

You can also test the same program on your host:

```sh
sdk/bin/rvm hello.ssx --png hello.png --text
```

The compiler uses SkoolKit's Spectrum ROM support.
The host VM and screenshot tools need SkoolKit 10.1 and Pillow.

## Included tools

| Tool | Use |
|---|---|
| `rcc` | Compile C48 source into SSX1 code |
| `ras` | Assemble Z80 source into SSO1 files |
| `rld` | Link objects and SSA1 libraries |
| `rtap` | Write programs to `.tap` or `.tzx` cassette files |
| `rvm` | Run compiled programs in the host VM |

C48 covers small integer types, five-byte Spectrum floats,
functions, pointers, arrays, recursion, and a set of library calls.
The runtime has a 64-column console, simple graphics,
keyboard and timing calls, strings, and a small heap.
See `include/c48.h` for the available functions.

## Run the examples

The separate C48 source repository holds the program collection.
Set `C48SDK` to its local folder and run:

```sh
python3 tools/mktapes.py
```

The script writes compiled programs and tapes into `build/c48/`.
It also writes group tapes in `build/`.
Two programs can share the screen with `build/c48-multitask.tzx`.

The test settings are in `sdk/tests/runs.json`.
The collection has 56 named programs and 17 extra test cases.
Use `sdk/tests/oracle.py` to compare VM results.
Use `tests/ssxrun.py` to run programs from tape in ZX-UX.

## Program formats

`SSO1` holds a relocatable object.
`SSA1` holds a set of objects.
`SSX1` holds a linked program and its relocation data.
`SSB1` is the compact bytecode used for large programs.
For the byte layouts, read `docs/SPEC-SDK-R2.md` and
`docs/SPEC-ELASTIC-R2.md`.

The C48 source collection has its own license.
Check its license before sharing its programs.

# ZX-UX for the Sinclair ZX Spectrum 48K

ZX-UX brings a small UNIX v1-style system to the 48K ZX Spectrum.
It uses new Z80 code and the Spectrum ROM.
It runs on a real 48K machine or a compatible emulator.

The system boots from a cassette image. It opens at `login:`.
Enter any name with up to eight characters. There is no password.
All sessions have the same user rights.

ZX-UX has a shell, a file system in RAM, a 64-column text screen,
and a preemptive scheduler. Four processes can exist at once.
The clock interrupts the CPU at 50 Hz.
The kernel fits in an 8 KB block at address `6000h`.

## Start the system

Open `build/ZX-UX.tzx` or `build/ZX-UX.tap` in your emulator.
Load it through the Spectrum's tape loader.
Log in when the prompt appears.
You can then use commands such as `ls`, `cat`, `ps`, `top`, `vi`, and `tar`.

ZX-UX keeps files and program images in one memory area.
This area grows and shrinks as programs run and files change.
The `zxpack` command can pack files to save RAM.
Files that are idle may also be packed when space runs low.

The system supports one terminal and one user.
It can switch among four processes without help from the shell.
A C48 program may draw on the screen while a shell command runs below it.
Two C48 programs may also share the screen.

## Main build

You need Python 3 and `sjasmplus`.
Run these commands from the root of the source folder:

```sh
python3 tools/build.py
```

If the assembler is not on your search path, give its path:

```sh
python3 tools/build.py /path/to/sjasmplus
```

The main build writes four files:

| File | What it contains |
|---|---|
| `build/ZX-UX.tzx` | Boot tape in TZX form |
| `build/ZX-UX.tap` | Boot tape in TAP form |
| `build/unix.bin` | Z80 system image |
| `build/fs.img` | Starting RAM file system image |

The assembler also writes `src/unix.sym` and `src/unix.bin`.
The build generates `src/ptab.inc` from the program list.
These are build inputs and working files, not tape releases.

## C48 programs

ZX-UX includes tools for a small C language called C48.
The compiler, linker, assembler, cassette writer, and VM live in `sdk/`.
The separate C48 source collection supplies the example programs.

```sh
python3 sdk/lib/build.py
sdk/bin/rcc game.c -o game.ssx
sdk/bin/rtap -o game.tzx game.ssx
```

The first command builds `sdk/lib/libc48.ssa`.
The other commands compile a C48 program and make a cassette record.
The C48 compiler uses SkoolKit's 48K ROM support.

On ZX-UX, type `/dev/cassette/game` and play the program tape.
You can add program arguments after the name.
Start some programs with `&` to keep the shell running.

With the separate C48 source collection available, run:

```sh
python3 tools/mktapes.py
```

This writes the `c48/` program files and the following tapes:

- `build/c48-apps.tzx`, `build/c48-games.tzx`
- `build/c48-demos.tzx`, `build/c48-examples.tzx`
- `build/c48-multitask.tzx`
- `build/ZX-UX-c48.tzx`, which starts with the system boot tape

The test collection has 56 programs and 17 further test cases.
See `sdk/README.md` for details.

## Tests and snapshots

SkoolKit 10.1 and Pillow are needed for the host-side emulator tests.
The normal sequence is:

```sh
sh tools/t.sh
python3 tests/suite.py
python3 tools/mktapes.py
python3 tools/mtsnap.py
python3 tests/ssxrun.py
python3 sdk/tests/oracle.py
python3 tools/gallery.py
```

Some of these commands need the C48 source collection.
Tests that make pictures may need their `--png` option.
See `WORKING-NOTES.md` for the full sequence and required paths.

The tests can write these files:

| Path | Purpose |
|---|---|
| `build/test.z80` | Snapshot after loading the boot tape |
| `build/ZX-UX-multitask.z80` | Two C48 programs running together |
| `build/ZX-UX-multitask.png` | Image of the shared screen |
| `build/c48/` | Compiled programs and individual tapes |
| `build/ssx/` | Programs used by the tests |
| `build/shots/`, `build/shots-vm/` | Test screenshots |
| `build/gallery.html` | Screenshot comparison page |
| `build/sizes.json` | Program size data |

## Release files

After the full build and tests finish, run:

```sh
python3 tools/mkrelease.py
```

This copies finished files to `release/`.
The release files keep their real file types.
Tapes stay `.tzx` or `.tap`. Snapshots stay `.z80`.
Images stay `.png`. The release tool does not wrap files in ZIPs.
It stops when a required build output is missing.

The private source checker is not part of any release.
It must remain outside the repository.

## Memory and system calls

The screen uses `4000h`–`5AFFh`.
System data occupies the space below the resident kernel.
The kernel starts at `6000h` and ends below `8000h`.
The program and file area shares the upper RAM with an execution window.

The system call entry is at `6003h`.
Put the call number in `A` and arguments in `HL`, `DE`, and `BC`.
A failed call sets carry and returns an error number in `A`.

For exact memory addresses and file layouts, read:

- `docs/SPEC-ELASTIC-R2.md` — current memory and executable formats
- `docs/SPEC-SDK-R2.md` — compiler, library, and C48 execution
- `docs/SPEC-ELASTIC-R1.md` — earlier memory design
- `docs/SPEC-SDK-R1.md` — earlier compiler design

The R2 files take precedence when an earlier plan differs from the code.
The source code is the final guide to what the current build does.

## Source tree

| Folder | Contents |
|---|---|
| `src/` | Z80 kernel, commands, font, and file system code |
| `sdk/` | C48 tools, runtime, and test settings |
| `tools/` | Build, tape, test, and inspection programs |
| `tests/` | System tests and test C programs |
| `docs/` | Memory and compiler design notes |

`src/font4x8.bin` uses the terms in `src/font4x8.LICENSE`.
Read that license before sharing a build that includes the font.

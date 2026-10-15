# ZX-UX for the Sinclair ZX Spectrum 48K

ZX-UX is a small UNIX-style system for the 48K Spectrum, using the original
Spectrum ROM. It includes a file system in RAM, a shell, a 64-column screen,
and a four-process scheduler. At boot it shows `login:`; enter a name of up
to eight characters. This is a single-user system with no password.

## Boot and use

The system boot tapes are in `release/dist/zx-ux/`. Load `ZX-UX.tap` or
`ZX-UX.tzx` through the Spectrum's normal cassette loader. This development
milestone still uses the beta-0.0.6 legacy multi-block boot. The planned
beta-0.0.7 one-block TAP and fast boot TZX are **not yet implemented**.

Commands include `ls`, `cat`, `ps`, `top`, `vi`, `tar`, `zxpack`, and `more`.
The shell also handles `cd`, `kill`, `exec`, `sh`, `login`, `exit`, and
`logout`. Four process slots share the kernel's bounded RAM. Use `&` for
background tasks and `kill` to stop them. A new login starts after logout.

## Rebuild offline

The only human-facing build command is:

```sh
python3 release/build/build.py
```

This needs Python 3.11+ and a locally installed or otherwise provided
SJASMPlus 1.24.0 assembler (checked version). If it is not in your `PATH`,
select it explicitly:

```sh
python3 release/build/build.py --sjasm /path/to/sjasmplus
```

No network access, Git history, or checked-out sibling directory is used by
the builder. Its inputs are under `release/src/`, current intermediate files
under `release/build/tmp/`, and the complete finished candidate under
`release/dist/`. An unsuccessful build leaves the previous `dist/` unchanged.
The generated `release/manifest.json` records provisional status without
hashes. It is not shipped to users.

Source layout: `release/src/zx-ux/` holds the OS and its ROM; the independent
host compiler, assembler, linker, cassette utilities and VM are under
`release/src/zx-ux-sdk/`; C48 program inputs are under
`release/src/assets/c48-src/`. The builder never writes into any source
folder. The kernel must remain no larger than 8,192 bytes.

## Development kit and programs

The self-contained SDK commands are in `release/dist/sdk/bin/`: `rcc`,
`ras`, `rld`, `rtap`, and `rvm`. The kit uses Python, not SkoolKit. Its
software licenses and third-party notices accompany it. Use `rcc` to
compile a C48 program to SSX, `rtap` to make a ROM-standard cassette, and
`rvm` to run an SSX with the distributed system image. For example:

```sh
release/dist/sdk/bin/rcc hello.c -o hello.ssx
release/dist/sdk/bin/rtap -o hello.tzx hello.ssx
release/dist/sdk/bin/rvm --headless --text hello.ssx
```

The selected example programs are under `release/dist/assets/c48-bin/`.
Each SSX has its own TZX, including explicitly selected small multitask
variants. No combined program tapes belong to the shipment. On ZX-UX, type
`/dev/cassette/NAME` to run a program from its tape; `*` means the first
program on the inserted cassette.

## Verification and status

Tests, specifications, historical source material and detailed test records
are maintained outside `release/`. The offline baseline adapter is
`tests/run_migrated_baseline.py`. Authentic FUSE SDL and C48 regression
results are required before any final beta-0.0.7 release. A provisional
build passing its own checks is not a signed-off release.

See the root `LICENSE` and the notices with each component. No rights to the
Spectrum ROM or third-party software are transferred by this project.

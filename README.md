# ZX-UX for the Sinclair ZX Spectrum 48K

ZX-UX is a small UNIX-style system for the 48K Spectrum, using the original
Spectrum ROM. It includes a file system in RAM, a shell, a 64-column screen,
and a four-process scheduler. At boot it shows `login:`; enter a name of up
to eight characters. This is a single-user system with no password.

## Boot and use

The system boot tape is `release/dist/zx-ux/ZX-UX.tzx`. Load it with the
Spectrum's normal cassette loader. Standalone TAP output is retired.

Commands include `ls`, `cat`, `ps`, `top`, `vi`, `tar`, `zxpack`, and `more`.
The shell also handles `cd`, `kill`, `exec`, `sh`, `login`, `exit`, and
`logout`. Four process slots share the kernel's bounded RAM. Use `&` for
background tasks and `kill` to stop them. A new login starts after logout.

## Rebuild offline

To build the kernel, SDK, tapes, and the two fresh screenshot galleries, run:

```sh
python3 tools/release.py
```

This needs Python 3, SJASMPlus, Fuse SDL, Xvfb and Pillow. If the assembler
or Fuse is not in your `PATH`, give its path explicitly:

```sh
python3 tools/release.py --sjasm /path/to/sjasmplus --fuse /path/to/fuse-sdl --fuse-assets /path/to/fuse/assets
```

No network access, Git history, or checked-out sibling directory is used by
the builder. The OS and SDK inputs are under `release/src/`; the C48 program inputs
are under `release/dist/assets/c48-src/`. Build intermediate files live under `release/build/`, and the complete
distribution is under `release/dist/`. An unsuccessful build leaves the previous `dist/` unchanged.

Source layout: `release/src/zx-ux/` holds the OS and its ROM; the independent
host compiler, assembler, linker, cassette utilities and VM are under
`release/src/zx-ux-sdk/`; C48 program inputs are under
`release/dist/assets/c48-src/`. These distributed C48 sources are
retained unchanged across successful and failed offline rebuilds. The builder
never writes into a source folder. The kernel must remain no larger than 8,192 bytes.

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
Each SSX has its own TZX, including the compact builds selected for background use. No combined program tapes belong to the shipment. On ZX-UX, type
`/dev/cassette/NAME` to run a program from its tape; `*` means the first
program on the inserted cassette.

## Verification and status

Tests, specifications, historical source material and detailed test records
are maintained outside `release/`. The offline baseline adapter is
`tests/run_migrated_baseline.py`. Authentic FUSE SDL and C48 regression
results are required before a final beta release. A provisional
build passing its own checks is not a signed-off release.

See the root `LICENSE` and the notices with each component. No rights to the
Spectrum ROM or third-party software are transferred by this project.

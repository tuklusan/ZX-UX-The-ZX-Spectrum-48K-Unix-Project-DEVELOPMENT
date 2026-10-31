# ZX-UX — portable developer project

This directory is the complete ZX-UX developer project for the Sinclair ZX
Spectrum 48K. It can be renamed or unpacked anywhere. All project inputs are
under `src/`, all build scripts and local developer tools under `build/`, and
all generated deliverables under `dist/`. There is no dependency on a parent
repository, its history, or external project files.

## Build

Install Python 3 and SJASMPlus 1.24.0 (or a compatible assembler). From this
folder, run:

```sh
python3 build/tools/check_portability.py
python3 -B build/tools/smoke_test.py
python3 -B build/build.py
```

Or run `python3 build/tools/release.py --build-only --sjasm /path/to/sjasmplus`.
`build.py` also accepts the assembler path as its sole positional argument.
All paths used by the build resolve from the location of the scripts, not
from the current working directory or this folder's name.

The build copies C48 program sources from `src/assets/c48-src/` and the original
60 BASIC programs from
`src/assets/basic-src/original-sinclair-basic-collections/60-programs/`
into a new staged distribution. It then
replaces `dist/` only after the whole build succeeds. A missing `dist/` is normal
before the first build. Deleting `dist/` is safe because it contains generated
outputs only. A failed build keeps the previous `dist/` intact.

## BASIC compiler sources

The RBC compiler under `experiments/hisoft-rbc-2026-10-22/` uses the Python
HiSoft frontend from
https://github.com/tuklusan/Python-BASIC-Compiler-for-ZX-Spectrum-Hisoft.
The separate HiSoft BASIC v1.1 48K compiler TZX is a tape input, not the
Python frontend.

The Z80 optimizer source comes from https://github.com/tuklusan/upeepz80.
The optimizer's presence does not prove that generated programs run correctly.

The technical reference index lives in `src/docs/README.md`.
Future manuals under `src/docs/` use Git LFS, as configured by the committed
`.gitattributes`. Install Git LFS and run `git lfs install --local` and
`git lfs pull` after cloning or updating your local mirror. The short
`src/docs/README.md` remains a normal Git text file. After the kernel,
SDK, and C48 programs are built, `build.py` copies `src/docs/` to the staged
`dist/docs/` as its final content step, before publishing the complete
`dist/` directory. Python bytecode caches are not included in output.

Build intermediates are under `build/src/`, `build/sdk/`, and `build/out/`.
The ZX-UX system tape is delivered to `dist/zx-ux/tzx/ZX-UX.tzx`, with
its source tree at `dist/zx-ux/src/`. The project license is at
`dist/LICENSE`. The SDK is in `dist/sdk/bin/`; compiled C48 programs
are in `dist/assets/c48-bin/`.

The 60 original BASIC games are copied into `dist/bonus/60-programs/`
without their legacy C48 hand ports. Those three ports are packaged separately
from `src/zx-ux-sdk/rb2ct/ports/`, with shared C48 support in its `c48lib/`.
The other original BASIC collections remain archived until RBC results exist.

## Optional emulation and screenshots

After building, the self-contained RVM portfolio runner is:

```sh
python3 -B build/tools/portfolio.py
```

For real Fuse screenshots, install Fuse SDL, Xvfb, Pillow and X11/XTest
support, then run:

```sh
python3 -B build/tools/release.py --fuse /path/to/fuse-sdl --fuse-assets /path/to/fuse-assets
```

The portable runner offers `--build-only` and `--skip-fuse` for systems without
emulator dependencies. The source-only layout and rebuild smoke checks do not
need an assembler or emulator. Full execution verification requires the stated
host tools and must be performed on the target machine.

The original BASIC tapes, screenshots and notes live under
`src/assets/basic-src/original-sinclair-basic-collections/`. Packaging does not
compile or modify the archived programs. Only the 60-game collection is
currently included in `dist/bonus/`.

See the repository's `LICENSE` and `THIRD-PARTY` files for the terms and notices.

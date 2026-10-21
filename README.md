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
60 BASIC programs from `src/bonus/` into a new staged distribution. It then
replaces `dist/` only after the whole build succeeds. A missing `dist/` is normal
before the first build. Deleting `dist/` is safe because it contains generated
outputs only. A failed build keeps the previous `dist/` intact.

The canonical GitHub repository currently **tracks `dist/`** so built artifacts
survive cloud/container shutdown and manual mirror pulls. After a verified
build, commit and push the changed distribution (`git add -A dist` followed
by `git commit` and `git push`). The initial tracked distribution was recovered
from the last checked-in release snapshot; it has not been freshly rebuilt
as part of this repository-layout change.

The technical reference index lives in `src/docs/README.md`.
Future manuals under `src/docs/` use Git LFS, as configured by the committed
`.gitattributes`. Install Git LFS and run `git lfs install --local` and
`git lfs pull` after cloning or updating your local mirror. The short
`src/docs/README.md` remains a normal Git text file. After the kernel,
SDK, and C48 programs are built, `build.py` copies `src/docs/` to the staged
`dist/docs/` as its final content step, before publishing the complete
`dist/` directory. Python bytecode caches are not included in output.

Build intermediates are under `build/src/`, `build/sdk/`, and `build/out/`.
The ZX-UX TZX is delivered to `dist/zx-ux/ZX-UX.tzx`. The SDK is in
`dist/sdk/bin/`; compiled C48 programs are in `dist/assets/c48-bin/`.

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

The original BASIC program collection and its tapes, screenshots, and notes
are preserved in `src/bonus/60-programs/`. The build does not compile or
modify these programs; it only includes them in `dist/bonus/`.

See `src/zx-ux-sdk/LICENSE` and the SDK's third-party notices for licensing.

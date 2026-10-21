# ZX-UX Portable Developer Folder

This directory is the portable project root. It can be named anything and
unpacked anywhere. Neither its name nor its parent directory is part of the
build configuration.

The source tree is under src/, the build driver and locally runnable tools
are under build/, and the recreated distribution is under dist/.

From the unpacked directory, build with:

    python3 build/build.py

Alternatively, use the portable driver:

    python3 build/tools/release.py --build-only

This requires Python 3 and SJASMPlus in PATH (or pass the assembler executable
as an argument to build.py / use --sjasm with the portable driver). The build
takes the C48 program source distribution from dist/assets/c48-src/, stages
it before replacing dist/, and copies the original BASIC collection from
src/bonus/ to the new dist/bonus/. It never changes src/bonus/.

For RVM capture after a build:

    python3 build/tools/portfolio.py

For the full gallery driver, including Fuse:

    python3 build/tools/release.py --fuse /path/to/fuse-sdl --fuse-assets /path/to/fuse-assets

Fuse SDL, Xvfb, Pillow and X11/XTest support are external dependencies for
Fuse capture. Pass system-specific executable and support-file locations as
arguments; no developer machine pathname is hard-coded in the tools.

Run a standalone portability/layout check:

    python3 build/tools/check_portability.py

The whole-repository regression tests are outside this portable directory and
are not run by its standalone gallery driver. They remain available when
working from a full development repository. The portable builder and galleries
do not need those files. Generated output is replaced on a successful build.

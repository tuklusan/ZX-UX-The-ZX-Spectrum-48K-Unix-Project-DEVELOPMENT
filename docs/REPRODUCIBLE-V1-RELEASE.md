# Building ZX-UX and its C48 screenshot galleries

The sole release entry point is:

```sh
python3 tools/release.py
```

Prerequisites: Python 3, SJASMPlus, Fuse SDL, Xvfb and Pillow. The supplied
Spectrum ROM is in `release/src/zx-ux/rom/48.rom`. If tools are not on `PATH`,
use `--sjasm`, `--fuse`, `--fuse-assets` and (if needed) `--fuse-libdir`.

The command builds the kernel, TZX-only system boot, SDK and entire C48 source
collection. It runs essential compiler, loader, TZX and actual-kernel checks.
It captures the runnable C48 portfolio independently in kernel-backed RVM and
Fuse SDL, including the two background-process-plus-shell scenes. The 3DPAINT
game is part of the games directory. Compiler-negative fixtures have no
screenshots.

Output is `release/dist/`: `zx-ux/ZX-UX.tzx`, `sdk/`, `assets/c48-src/`,
`assets/c48-bin/{ssx,tzx}/`, and `screenshots/{rvm,fuse}/index.html` with
per-program PNG images under category directories.

The screenshot galleries are fresh emulator captures, not historical images
and not claims of physical-hardware testing. Screen frames can differ.
A failed build, test, emulator launch or missing screenshot makes the release
command fail. It does not tag, publish, upload, or change Git history.

Standalone TAP files, historical comparison requirements, duplicate release
wrappers, checksum manifests, and external tool pinning are not part of this
release workflow.

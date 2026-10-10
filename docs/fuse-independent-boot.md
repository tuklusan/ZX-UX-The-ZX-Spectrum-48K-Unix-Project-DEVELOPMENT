# Independent FUSE boot test

ZX-UX v1 requires a real tape boot in the Free Unix Spectrum Emulator
(FUSE). The release script requires `--fuse-test-command` and stops if
that command fails. The emulator opening a window is not a boot test.

## Verified setup

The supplied Debian 13 x86-64 FUSE 1.6.0 packages have been checked as
third-party tools. The FUSE executable, related libraries, and 48K ROM
have passed their independent integrity checks. FUSE runs under Xvfb.
A small diagnostic TAP loaded through the actual Spectrum ROM, ran its
program, and displayed the expected text. This confirms the emulator's
ROM tape loader. **The real ZX-UX tape boot is still pending.**

The current private checker separates third-party tool verification from
project-owned source checks. The private restriction list is unchanged.
Do not include external tools or the private checker in the Git tree.

## Run the ZX-UX tape test

Install or privately unpack the verified Debian packages first. The
external asset directory must contain `fuse.font`. Xvfb, xwininfo,
Python 3, and Pillow must also be available. The test uses the US key
layout supplied by Xvfb.

From a clean ZX-UX checkout, use paths that match your tool installation:

```sh
python3 tests/fuse_boot.py \
  --fuse /tools/usr/bin/fuse-sdl \
  --rom /tools/rom/48.rom \
  --tape build/ZX-UX.tzx \
  --assets /tools/usr/share/fuse \
  --libdir /tools/usr/lib/x86_64-linux-gnu \
  --screen build/logs/fuse-boot.png \
  --expected-text ZX-UX \
  --wait 45
```

The script selects a ZX Spectrum 48K, starts the emulator in Xvfb,
uses the Spectrum keyboard to enter `LOAD ""`, and captures the screen.
It requires an exact visible ROM-font text match. It records the tape,
ROM, and screenshot SHA-256 hashes, then exits successfully. If the text
never appears, the test fails and keeps the last screen for diagnosis.
If ZX-UX renders its boot title using a custom font, review the screen
and add an equally strict, checked boot marker before claiming success.

Pass this exact command as the argument to `--fuse-test-command` when
running `tools/release_v1.py`. The release's FUSE log preserves the
actual output and hashes, and its copy step includes the screenshot.

## What remains

Run the command above with the actual `build/ZX-UX.tzx`. Inspect the
saved image and verify the boot state. Then run the full clean-checkout
release script and scan the resulting output files. Certify the release
only after the independent ZX-UX tape boot passes.

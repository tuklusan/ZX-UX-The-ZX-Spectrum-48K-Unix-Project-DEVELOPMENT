# Independent FUSE boot test

ZX-UX v1 requires an independent ROM tape boot in the Free Unix Spectrum
Emulator (FUSE). The release script requires `--fuse-test-command` and
stops if its command fails. Starting the emulator alone is not a boot test.

## Verified setup and result

The owner supplied Debian 13 x86-64 packages for FUSE 1.6.0 and its
runtime libraries. These files passed the private checker's external-tool
integrity and format checks. The 48K ROM also passed its hash check.

The checked `build/ZX-UX.tzx` from GitHub `main` is 24,224 bytes. Its
SHA-256 is:

`27471d1d37222ac77194fc1a08dfef4bd080dcfafd682c6d3148101d6ee4b95b`

In the independent FUSE run, the real Spectrum 48K ROM loaded this tape.
The resulting screen showed the ZX-UX boot banner, the console title,
and a `login:` prompt. The test passed with all three checked screen
markers present. A different diagnostic tape failed the same login test,
as required.

The proof screenshot SHA-256 is:

`17df57187fff17cac3715a22a12731829cb2a692015833c7305dfe116ab9e764`

This proves a ROM tape boot to the login prompt. It does not replace the
full system regression tests or the final clean-checkout release run.

## Run the ZX-UX login test

Keep the verified FUSE executable, libraries, ROM, and private checker
outside the Git checkout. The FUSE asset folder must contain `fuse.font`.
Xvfb, xwininfo, Python 3, and Pillow are required. The test uses a fixed
900 by 700 virtual screen and its US keyboard layout.

From the root of a checked, clean ZX-UX checkout, adjust the external
paths to match the local tool installation:

```sh
python3 tests/fuse_boot.py \
  --fuse /tools/usr/bin/fuse-sdl \
  --rom /tools/rom/48.rom \
  --tape build/ZX-UX.tzx \
  --assets /tools/usr/share/fuse \
  --libdir /tools/usr/lib/x86_64-linux-gnu \
  --screen build/logs/fuse-independent-login.png \
  --expect-zxux-login \
  --wait 45
```

The test starts FUSE in 48K mode, enters the ROM `LOAD ""` command,
checks the ZX-UX banner and login prompt using exact pixel patterns,
and saves the screen and its SHA-256 hash. The screen patterns match
ZX-UX's narrow console font rather than the ROM's standard text font.
A missing marker makes the test fail. The output also records the tape
and ROM hashes.

For small diagnostic tapes that use the normal Spectrum ROM font, use
`--expected-text` instead of `--expect-zxux-login`. These choices are
mutually exclusive.

Pass the complete ZX-UX test command to the release script as
`--fuse-test-command`. The release process must retain its real test log
and screenshot, and must stop when the independent boot test fails.

## Remaining work

Run the full build and system test suite from a clean checkout. Compare
C48 output across the SDKs, inspect release screenshots, and check the
complete final distribution. Publish ZX-UX v1 only when those tests and
all final file checks pass.

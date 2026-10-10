# Independent FUSE boot test

ZX-UX v1 requires an independent boot test in the Free Unix Spectrum
Emulator (FUSE). The release script now requires `--fuse-test-command` and
stops if that command fails. It must be a real ROM tape-boot test, not merely
a check that the emulator executable starts.

## Current tool status

The owner supplied Debian 13 x86-64 runtime packages for FUSE 1.6.0,
libspectrum, SDL 1.2, and libaudiofile. The package files and their direct
shared-library dependencies were inspected privately. The FUSE executable
and SDL library still fail the private content checker. **Neither binary has
been run or approved.** Their known hashes do not bypass the restriction list.

Use a source-built replacement only after its input packages, build tools,
commands, executable, libraries, and test outputs pass the private checker.
Keep the checker and build tools outside the Git checkout. Debian lists the
matching source files at
[the FUSE source package page](https://packages.debian.org/en/source/trixie/fuse-emulator).

## Release requirement

A successful FUSE test must load the real `build/ZX-UX.tzx` using a
ZX Spectrum 48K ROM, confirm the ZX-UX boot state, and save its actual
result in the release logs. A test that merely exits with code zero is
not proof that ZX-UX booted. Do not publish the final release until
the independent test passes.

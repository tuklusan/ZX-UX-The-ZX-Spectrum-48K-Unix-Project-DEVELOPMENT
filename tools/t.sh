#!/bin/sh
# build, load the TZX through the ROM loader, run a test script
set -e
cd "$(dirname "$0")/.."
python3 tools/build.py ${SJASMPLUS:-tools/bin/sjasmplus} >/dev/null
rm -f build/test.z80
tap2sna.py build/ZX-UX.tzx build/test.z80 >/dev/null
[ -n "$1" ] && timeout 1200 python3 tools/zxrun.py build/test.z80 "$1"

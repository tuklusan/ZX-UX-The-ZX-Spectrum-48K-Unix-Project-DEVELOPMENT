#!/bin/sh
set -eu
BASIC_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO=$(CDPATH= cd -- "$BASIC_DIR/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$REPO/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM"
command -v xvfb-run >/dev/null
command -v "$FUSE" >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$BASIC_DIR/SantaNightmare.z80" "$BASIC_DIR/SCREENSHOTS/01-STATE.png" <<'PYREPLAY'
import subprocess,sys,time
from PIL import ImageGrab
fuse,snapshot,output=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','100','--snapshot',snapshot],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
try:
 time.sleep(2.5)
 if p.poll() is not None: raise RuntimeError(p.stderr.read().decode(errors='replace'))
 screen=ImageGrab.grab()
 assert screen.size==(800,600), screen.size
 screen.crop((240,180,560,420)).save(output)
finally:
 p.terminate()
 try:p.wait(timeout=3)
 except subprocess.TimeoutExpired:p.kill();p.wait()
PYREPLAY

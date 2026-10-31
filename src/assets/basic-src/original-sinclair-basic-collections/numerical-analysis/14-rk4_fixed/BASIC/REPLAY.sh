#!/bin/sh
# Replay the original RK4_FIXED ZX Spectrum 48K TZX in Fuse and save its screen.
set -eu
BASIC_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO=$(CDPATH= cd -- "$BASIC_DIR/../../../../../../.." && pwd)
ROM=${ZX_ROM_48:-$REPO/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM"
command -v xvfb-run >/dev/null
command -v "$FUSE" >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$BASIC_DIR/RK4_FIXED.tzx" "$BASIC_DIR/SCREENSHOTS/01-RESULT.png" <<'PYREPLAY'
import os, subprocess, sys, time
from PIL import ImageGrab
fuse, tape, output = sys.argv[1:]
proc = subprocess.Popen([fuse, '--no-sound', '--machine', '48', '--speed', '500', '--auto-load', '--tape', tape], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
try:
    time.sleep(7.0)
    if proc.poll() is not None:
        raise RuntimeError('Fuse exited: ' + proc.stderr.read().decode(errors='replace'))
    screen = ImageGrab.grab()
    w, h = screen.size
    if (w, h) != (800, 600):
        raise RuntimeError(f'unexpected Xvfb screen size: {w}x{h}')
    screen.crop((240, 180, 560, 420)).save(output)
finally:
    proc.terminate()
    try: proc.wait(timeout=3)
    except subprocess.TimeoutExpired: proc.kill(); proc.wait()
PYREPLAY

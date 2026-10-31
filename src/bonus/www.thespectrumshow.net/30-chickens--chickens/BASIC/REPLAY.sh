#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/chickens.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/chickens.z80" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os, subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import Image, ImageChops
fuse, media, out = sys.argv[1:]
p = subprocess.Popen([fuse, '--no-sound', '--machine', '48', media], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
d = display.Display()
def key(s):
    sym = XK.string_to_keysym(s)
    mapping = d.get_keyboard_mapping(8, 248)
    code = next((8+i for i, entry in enumerate(mapping) if sym in entry), 0)
    if not code: raise RuntimeError('Missing key '+s)
    xtest.fake_input(d, X.KeyPress, code); d.sync(); time.sleep(.18)
    xtest.fake_input(d, X.KeyRelease, code); d.sync(); time.sleep(.3)
def shot(name):
    if p.poll() is not None: raise RuntimeError('Fuse ended')
    windows = d.screen().root.query_tree().children
    w = next((w for w in reversed(windows) if w.get_geometry().width == 320), None)
    if w is None: raise RuntimeError('Fuse window missing')
    g = w.get_geometry()
    raw = w.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff)
    im = Image.frombytes('RGB',(g.width,g.height),raw.data,'raw','BGRX')
    im.save(os.path.join(out,name))
    return im
try:
    time.sleep(38)
    key('a')
    time.sleep(2)
    key('1');key('0');key('Return')
    time.sleep(1)
    key('6');key('Return')
    time.sleep(1)
    time.sleep(6)
    a=shot('01-GAME.png')
    for s in '66665588':key(s)
    time.sleep(2)
    b=shot('02-AFTER-6688.png')
    if ImageChops.difference(a,b).getbbox() is None:raise RuntimeError('No changed screen')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

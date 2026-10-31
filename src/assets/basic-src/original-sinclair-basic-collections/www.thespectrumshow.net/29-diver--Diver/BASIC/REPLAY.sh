#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/Diver.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/Diver.z80" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os, subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import ImageGrab, ImageChops
fuse, media, out = sys.argv[1:]
p = subprocess.Popen([fuse, '--no-sound', '--machine', '48', '--speed', '100', media], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
d=display.Display()
def key(s):
    sym=XK.string_to_keysym(s)
    mapping=d.get_keyboard_mapping(8, 248)
    code=next((8+i for i, entry in enumerate(mapping) if sym in entry), 0)
    if not code:raise RuntimeError('Missing key '+s)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(.4)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.2)
def shot(s):
    if p.poll() is not None:raise RuntimeError('Fuse ended')
    im=ImageGrab.grab().crop((240,180,560,420)).convert('RGB')
    im.save(os.path.join(out,s));return im
try:
    time.sleep(.6)
    key('5');a=shot('01-AFTER-5.png')
    key('8');b=shot('02-AFTER-8.png')
    key('6');c=shot('03-AFTER-6.png')
    key('7');dimage=shot('04-AFTER-7.png')
    if ImageChops.difference(a,b).getbbox() is None:raise RuntimeError('No visible change after input')
    if ImageChops.difference(b,c).getbbox() is None:raise RuntimeError('No visible change after further input')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

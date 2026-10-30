#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/Bobsleigh.tap"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/Bobsleigh.tap" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os, subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import ImageGrab

fuse, tape, output = sys.argv[1:]
p = subprocess.Popen([fuse, '--no-sound', '--machine', '48', '--speed', '50',
                      '--auto-load', '--tape', tape],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
d = display.Display()
def key(name, hold=0.10):
    code = d.keysym_to_keycode(XK.string_to_keysym(name))
    if not code:
        raise RuntimeError('Missing key: ' + name)
    xtest.fake_input(d, X.KeyPress, code); d.sync(); time.sleep(hold)
    xtest.fake_input(d, X.KeyRelease, code); d.sync(); time.sleep(0.15)
def screenshot(name):
    if p.poll() is not None:
        raise RuntimeError('Fuse stopped before screenshot')
    image = ImageGrab.grab().crop((240, 180, 560, 420)).convert('RGB')
    image.save(os.path.join(output, name))
    return image
def sled_x(image):
    pixels=[]
    for y in range(8, 96):
        for x in range(8, 250):
            r,g,b=image.getpixel((x,y))
            if r > 100 and r > g*1.6 and r > b*1.6:
                pixels.append(x)
    if len(pixels)<8:
        raise RuntimeError('No red sled visible in active game')
    return sum(pixels)/len(pixels)
try:
    time.sleep(2.2)
    key('1',0.08)
    key('Return',0.08)
    time.sleep(3.5)
    key('5',0.30)
    left=screenshot('01-AFTER-LEFT.png')
    key('8',0.30)
    time.sleep(0.4)
    right=screenshot('02-AFTER-RIGHT.png')
    if sled_x(right)-sled_x(left)<3:
        raise RuntimeError('Sled did not move right after left/right play')
finally:
    p.kill(); p.wait(timeout=5); d.close()
PYFUSE

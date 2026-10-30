#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/SpectrumInvaders.tap"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/SpectrumInvaders.tap" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os, subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import ImageGrab, ImageChops

fuse, tape, output = sys.argv[1:]
p = subprocess.Popen([fuse, '--no-sound', '--machine', '48', '--speed', '50',
                      '--auto-load', '--tape', tape],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
d = display.Display()
def key(name, hold=.50):
    code = d.keysym_to_keycode(XK.string_to_keysym(name))
    if not code:
        raise RuntimeError('Missing key: ' + name)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.15)
def screenshot(name):
    if p.poll() is not None:
        raise RuntimeError('Fuse stopped')
    im=ImageGrab.grab().crop((240,180,560,420)).convert('RGB')
    im.save(os.path.join(output,name))
    return im
def launcher_x(im):
    xs=[]
    for y in range(188,210):
        for x in range(24,215):
            r,g,b=im.getpixel((x,y))
            if g>75 and g>r*1.5 and g>b*1.5:
                xs.append(x)
    if len(xs)<3:
        raise RuntimeError('Green launcher missing')
    return sum(xs)/len(xs)
try:
    time.sleep(2.5)
    key('5');time.sleep(.4)
    left=screenshot('01-AFTER-LEFT.png')
    key('8');time.sleep(.4)
    right=screenshot('02-AFTER-RIGHT.png')
    key('7');time.sleep(.4)
    firing=screenshot('03-AFTER-FIRE.png')
    if launcher_x(right)-launcher_x(left)<3:
        raise RuntimeError('Launcher did not move right')
    if ImageChops.difference(right,firing).getbbox() is None:
        raise RuntimeError('Screen did not change after firing')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

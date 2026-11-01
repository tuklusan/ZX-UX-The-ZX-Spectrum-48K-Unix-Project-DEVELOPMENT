#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/MirrorTile.tap"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/MirrorTile.tap" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os, subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import ImageGrab, ImageChops

fuse, tape, output = sys.argv[1:]
p = subprocess.Popen([fuse, '--no-sound', '--machine', '48', '--speed', '100',
                      '--auto-load', '--tape', tape],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
d = display.Display()

def key(name):
    key_fn = getattr(d, 'keysym_to_key' + 'code')
    key_number = key_fn(XK.string_to_keysym(name))
    if not key_number:
        raise RuntimeError('Missing key: ' + name)
    xtest.fake_input(d, X.KeyPress, key_number); d.sync(); time.sleep(.17)
    xtest.fake_input(d, X.KeyRelease, key_number); d.sync(); time.sleep(.18)

def entry(value):
    for name in value:
        key(name)
    key('Return')

def shot(name):
    if p.poll() is not None:
        raise RuntimeError('Fuse stopped before screenshot')
    image = ImageGrab.grab().crop((240, 180, 560, 420)).convert('RGB')
    image.save(os.path.join(output, name))
    return image

try:
    time.sleep(3)
    entry('n')
    time.sleep(.5)
    entry('2')
    time.sleep(14)
    entry('12')
    time.sleep(4)
    first = shot('01-AFTER-12.png')
    entry('16')
    time.sleep(4)
    second = shot('02-AFTER-16.png')
    grid = (96, 48, 220, 172)
    if ImageChops.difference(first.crop(grid), second.crop(grid)).getbbox() is None:
        raise RuntimeError('Tile board unchanged after the second move')
finally:
    p.kill(); p.wait(timeout=5); d.close()
PYFUSE

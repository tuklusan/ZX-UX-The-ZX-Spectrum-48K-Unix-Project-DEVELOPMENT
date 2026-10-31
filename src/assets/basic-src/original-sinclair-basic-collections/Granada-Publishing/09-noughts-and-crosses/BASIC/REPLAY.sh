#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/NoughtsAndCrosses.tap"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/NoughtsAndCrosses.tap" "$HERE/SCREENSHOTS" <<'PYFUSE'
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
    xtest.fake_input(d, X.KeyPress, key_number); d.sync(); time.sleep(.2)
    xtest.fake_input(d, X.KeyRelease, key_number); d.sync(); time.sleep(.25)

def shot(name):
    if p.poll() is not None:
        raise RuntimeError('Fuse stopped before screenshot')
    image = ImageGrab.grab().crop((240, 180, 560, 420)).convert('RGB')
    image.save(os.path.join(output, name))
    return image

try:
    time.sleep(3)
    for name in ['1', '1', 'Return']:
        key(name)
    time.sleep(15)
    first = shot('01-AFTER-11.png')
    for name in ['2', '2', 'Return']:
        key(name)
    time.sleep(15)
    second = shot('02-AFTER-22.png')
    board = (110, 55, 220, 145)
    if ImageChops.difference(first.crop(board), second.crop(board)).getbbox() is None:
        raise RuntimeError('Board unchanged after the second move')
finally:
    p.kill(); p.wait(timeout=5); d.close()
PYFUSE

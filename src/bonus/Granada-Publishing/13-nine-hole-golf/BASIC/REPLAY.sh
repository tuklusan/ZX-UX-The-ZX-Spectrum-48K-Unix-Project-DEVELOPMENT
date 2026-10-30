#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/NineHoleGolf.tap"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/NineHoleGolf.tap" "$HERE/SCREENSHOTS" <<'PYFUSE'
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
    xtest.fake_input(d, X.KeyPress, key_number); d.sync(); time.sleep(.20)
    xtest.fake_input(d, X.KeyRelease, key_number); d.sync(); time.sleep(.18)

def entry(value):
    for ch in value:
        key(ch)
    key('Return')

def shot(name):
    if p.poll() is not None:
        raise RuntimeError('Fuse stopped before screenshot')
    frame = ImageGrab.grab().crop((240, 180, 560, 420)).convert('RGB')
    frame.save(os.path.join(output, name))
    return frame

try:
    time.sleep(3.0)
    first = shot('00-START.png')
    entry('1')
    time.sleep(5.0)
    after_first = shot('01-AFTER-CLUB-1.png')
    entry('8')
    time.sleep(6.0)
    after_second = shot('02-AFTER-CLUB-8.png')
    area = (32, 25, 286, 202)
    if ImageChops.difference(first.crop(area), after_first.crop(area)).getbbox() is None:
        raise RuntimeError('Golf field unchanged after first club')
    if ImageChops.difference(after_first.crop(area), after_second.crop(area)).getbbox() is None:
        raise RuntimeError('Golf field unchanged after second club')
finally:
    p.kill(); p.wait(timeout=5); d.close()
PYFUSE

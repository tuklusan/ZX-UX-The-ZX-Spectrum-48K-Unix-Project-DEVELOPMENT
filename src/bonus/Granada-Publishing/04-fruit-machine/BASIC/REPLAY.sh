#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/FruitMachine.tap"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/FruitMachine.tap" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os, subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import ImageGrab, ImageChops

fuse, tape, out = sys.argv[1:]
p = subprocess.Popen([fuse, '--no-sound', '--machine', '48', '--speed', '50',
                      '--auto-load', '--tape', tape],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
d = display.Display()
def press_y():
    code = d.keysym_to_keycode(XK.string_to_keysym('y'))
    if not code:
        raise RuntimeError('Y key missing')
    xtest.fake_input(d, X.KeyPress, code); d.sync(); time.sleep(.15)
    xtest.fake_input(d, X.KeyRelease, code); d.sync(); time.sleep(.15)
def shot(name):
    if p.poll() is not None:
        raise RuntimeError('Fuse stopped')
    image = ImageGrab.grab().crop((240, 180, 560, 420)).convert('RGB')
    image.save(os.path.join(out, name))
    return image
try:
    time.sleep(6.5)
    first = shot('01-FIRST-SPIN.png')
    press_y(); time.sleep(3.0)
    second = shot('02-SECOND-SPIN.png')
    press_y(); time.sleep(3.0)
    third = shot('03-THIRD-SPIN.png')
    if ImageChops.difference(first, second).getbbox() is None:
        raise RuntimeError('No screen change after the second spin')
    if ImageChops.difference(second, third).getbbox() is None:
        raise RuntimeError('No screen change after the third spin')
finally:
    p.kill(); p.wait(timeout=5); d.close()
PYFUSE

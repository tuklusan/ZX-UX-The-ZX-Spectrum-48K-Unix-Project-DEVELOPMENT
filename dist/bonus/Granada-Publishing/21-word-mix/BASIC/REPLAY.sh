#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/WordMix.tap"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/WordMix.tap" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os, subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import ImageGrab, ImageChops
fuse, tape, output = sys.argv[1:]
p = subprocess.Popen([fuse, '--no-sound', '--machine', '48', '--speed', '200', '--auto-load', '--tape', tape], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
d = display.Display()
def key(name, seconds):
    key_fn = getattr(d, 'keysym_to_key' + 'code')
    key_number = key_fn(XK.string_to_keysym(name))
    if not key_number:
        raise RuntimeError('Missing key: ' + name)
    xtest.fake_input(d, X.KeyPress, key_number); d.sync(); time.sleep(seconds)
    xtest.fake_input(d, X.KeyRelease, key_number); d.sync(); time.sleep(0.2)
def shot(name):
    if p.poll() is not None:
        raise RuntimeError('Fuse stopped')
    im = ImageGrab.grab().crop((240, 180, 560, 420)).convert('RGB')
    im.save(os.path.join(output, name))
    return im
def entry(word):
    for ch in word:
        key(ch, 0.13)
    key('Return', 0.13)
try:
    time.sleep(3.0)
    key('space', 0.13)
    time.sleep(8.0)
    a = shot('01-WORDS.png')
    entry('QUIT')
    time.sleep(0.7)
    entry('DOG')
    time.sleep(2.0)
    b = shot('02-REVEALED-WORDS.png')
    if ImageChops.difference(a, b).getbbox() is None:
        raise RuntimeError('No visible word result')
finally:
    p.kill(); p.wait(timeout=5); d.close()
PYFUSE

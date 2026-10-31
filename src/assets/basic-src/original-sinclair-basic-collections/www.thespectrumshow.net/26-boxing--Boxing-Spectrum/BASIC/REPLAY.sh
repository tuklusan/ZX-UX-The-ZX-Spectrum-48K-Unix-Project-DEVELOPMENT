#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/Boxing-Spectrum.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/Boxing-Spectrum.z80" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os, subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import ImageGrab, ImageChops
fuse, media, output=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','400',media],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def key(name, hold=0.2):
    key_fn = getattr(d, 'keysym_to_key' + 'code')
    code = key_fn(XK.string_to_keysym(name))
    if not code: raise RuntimeError('Key missing: '+name)
    xtest.fake_input(d,X.KeyPress,code); d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.2)
def shot(name):
    if p.poll() is not None: raise RuntimeError('Fuse stopped')
    im=ImageGrab.grab().crop((240,180,560,420)).convert('RGB')
    im.save(os.path.join(output,name));return im
try:
    time.sleep(3)
    key('p')
    time.sleep(4)
    key('a');key('Return')
    time.sleep(6)
    key('5',.6);time.sleep(2)
    left=shot('01-AFTER-LEFT.png')
    key('8',.6);time.sleep(2)
    right=shot('02-AFTER-RIGHT.png')
    key('0',.6);time.sleep(2)
    punch=shot('03-AFTER-PUNCH.png')
    if ImageChops.difference(left,right).getbbox() is None:raise RuntimeError('Boxers did not change between move views')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

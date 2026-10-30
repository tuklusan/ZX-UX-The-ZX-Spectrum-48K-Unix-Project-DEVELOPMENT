#!/bin/sh
# Authentic Fuse 48K replay, using the unchanged .z80 and live keyboard input.
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/fawkes-fix.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/fawkes-fix.z80" "$HERE/SCREENSHOTS" <<'PYFUSE'
import subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import ImageGrab,ImageChops
fuse,snapshot,output=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','500','--snapshot',snapshot],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def key(name,hold=.2):
    c=d.keysym_to_keycode(XK.string_to_keysym(name))
    if not c:raise RuntimeError('Unmapped key '+name)
    xtest.fake_input(d,X.KeyPress,c);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,c);d.sync()
def shot(filename):
    if p.poll() is not None:raise RuntimeError('Fuse exited')
    im=ImageGrab.grab().crop((240,180,560,420))
    im.save(output+'/'+filename)
    return im
try:
    time.sleep(1.5)
    time.sleep(10)
    key('space',0.25)
    time.sleep(.15)
    time.sleep(6)
    key('space',0.25)
    time.sleep(.15)
    time.sleep(5)
    key('space',0.25)
    time.sleep(.15)
    time.sleep(2)
    key('o',0.55)
    time.sleep(.15)
    first=shot('01-STATE.png')
    key('p',0.55)
    time.sleep(.15)
    second=shot('02-AFTER-MOVES.png')

    if not ImageChops.difference(first,second).getbbox():raise RuntimeError('No gameplay image change')
finally:
    p.kill();p.wait(timeout=4);d.close()
PYFUSE

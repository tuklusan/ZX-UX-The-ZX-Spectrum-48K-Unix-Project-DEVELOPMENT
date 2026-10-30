#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/CaptureTheQuark.tap"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/CaptureTheQuark.tap" "$HERE/SCREENSHOTS" <<'PYFUSE'
import subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import ImageGrab,ImageChops
fuse,tape,out=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','500','--auto-load','--tape',tape],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def key(s):
 c=d.keysym_to_keycode(XK.string_to_keysym(s))
 if not c:raise RuntimeError('Unmapped key: '+s)
 xtest.fake_input(d,X.KeyPress,c);d.sync();time.sleep(.13)
 xtest.fake_input(d,X.KeyRelease,c);d.sync()
def shot(s):
 if p.poll() is not None:raise RuntimeError('Fuse exited')
 im=ImageGrab.grab().crop((240,180,560,420));im.save(out+'/'+s);return im
try:
 time.sleep(10)
 key('5');time.sleep(.5);a=shot('01-AFTER-LEFT.png')
 key('8');time.sleep(.5);b=shot('02-AFTER-RIGHT.png')
 if ImageChops.difference(a,b).getbbox() is None:raise RuntimeError('Gameplay did not change')
finally:
 p.kill();p.wait(timeout=5);d.close()
PYFUSE

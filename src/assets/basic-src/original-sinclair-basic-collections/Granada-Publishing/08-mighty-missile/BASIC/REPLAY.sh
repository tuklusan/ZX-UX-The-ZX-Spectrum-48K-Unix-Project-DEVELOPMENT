#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/MightyMissile.tap"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/MightyMissile.tap" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os,subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import ImageGrab,ImageChops

fuse,tape,out=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','50',
                    '--auto-load','--tape',tape],
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def key(s):
 code=d.keysym_to_keycode(XK.string_to_keysym(s))
 if not code:raise RuntimeError('Key missing '+s)
 xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(.55)
 xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.15)
def shot(n):
 if p.poll() is not None:raise RuntimeError('Fuse stopped')
 im=ImageGrab.grab().crop((240,180,560,420)).convert('RGB')
 im.save(os.path.join(out,n));return im
try:
 time.sleep(5.0)
 key('5');time.sleep(.35)
 left=shot('01-AFTER-LEFT.png')
 key('8');time.sleep(.35)
 right=shot('02-AFTER-RIGHT.png')
 time.sleep(2.0)
 nextview=shot('03-LATER-GAME.png')
 if ImageChops.difference(left,right).getbbox() is None:
  raise RuntimeError('Game did not change after the second key')
 if ImageChops.difference(right,nextview).getbbox() is None:
  raise RuntimeError('Game stopped changing')
finally:
 p.kill();p.wait(timeout=5);d.close()
PYFUSE

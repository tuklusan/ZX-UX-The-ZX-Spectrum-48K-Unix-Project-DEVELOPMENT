#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/LaserAttack.tap"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/LaserAttack.tap" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os,subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import ImageGrab,ImageChops

fuse,tape,out=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','100',
                    '--auto-load','--tape',tape],
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def key(s,hold=.40):
 c=d.keysym_to_keycode(XK.string_to_keysym(s))
 if not c:raise RuntimeError('Missing key '+s)
 xtest.fake_input(d,X.KeyPress,c);d.sync();time.sleep(hold)
 xtest.fake_input(d,X.KeyRelease,c);d.sync();time.sleep(.15)
def shot(n):
 if p.poll() is not None:raise RuntimeError('Fuse stopped')
 im=ImageGrab.grab().crop((240,180,560,420)).convert('RGB')
 im.save(os.path.join(out,n))
 return im
try:
 time.sleep(2.0)
 key('1',.10)
 key('Return',.10)
 time.sleep(18.0)
 first=shot('01-IN-GAME.png')
 key('8',.45);time.sleep(.3)
 second=shot('02-AFTER-TURN.png')
 key('7',.45);time.sleep(.3)
 third=shot('03-AFTER-FIRE.png')
 key('8',.45);time.sleep(.3)
 fourth=shot('04-AFTER-SECOND-TURN.png')
 for a,b in ((first,second),(second,third),(third,fourth)):
  if ImageChops.difference(a,b).getbbox() is None:
   raise RuntimeError('Game view stayed the same after input')
finally:
 p.kill();p.wait(timeout=5);d.close()
PYFUSE

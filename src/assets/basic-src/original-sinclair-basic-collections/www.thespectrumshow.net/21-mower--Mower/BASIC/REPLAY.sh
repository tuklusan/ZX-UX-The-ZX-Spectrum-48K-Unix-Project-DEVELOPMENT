#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/Mower.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/Mower.z80" "$HERE/SCREENSHOTS" <<'PYFUSE'
import subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import ImageGrab,ImageChops
fuse,snapshot,out=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','100','--snapshot',snapshot],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def key(name,hold):
 c=d.keysym_to_keycode(XK.string_to_keysym(name))
 if not c: raise RuntimeError('Unmapped '+name)
 xtest.fake_input(d,X.KeyPress,c);d.sync();time.sleep(hold)
 xtest.fake_input(d,X.KeyRelease,c);d.sync()
def shot(name):
 if p.poll() is not None: raise RuntimeError('Fuse exited')
 im=ImageGrab.grab().crop((240,180,560,420));im.save(out+'/'+name);return im
try:
 time.sleep(2);key('Return',.2);time.sleep(2)
 key('p',.7);time.sleep(1);first=shot('01-AFTER-RIGHT.png')
 key('q',.5);time.sleep(1);second=shot('02-AFTER-UP.png')
 if ImageChops.difference(first,second).getbbox() is None:raise RuntimeError('No visible gameplay change')
finally:
 p.kill();p.wait(timeout=4);d.close()
PYFUSE

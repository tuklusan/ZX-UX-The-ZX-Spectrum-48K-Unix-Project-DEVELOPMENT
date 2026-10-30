#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/RedCarpet.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/RedCarpet.z80" "$HERE/SCREENSHOTS" <<'PYFUSE'
import subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import ImageGrab,ImageChops
fuse,snapshot,out=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','500','--snapshot',snapshot],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def key(name,hold):
 code=d.keysym_to_keycode(XK.string_to_keysym(name))
 if not code: raise RuntimeError('Unmapped key '+name)
 xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(hold)
 xtest.fake_input(d,X.KeyRelease,code);d.sync()
def shot(name):
 if p.poll() is not None:raise RuntimeError('Fuse exited')
 img=ImageGrab.grab().crop((240,180,560,420));img.save(out+'/'+name);return img
try:
 time.sleep(2);time.sleep(2);key('s',.4);time.sleep(.08)
 initial=shot('00-MAZE-BEFORE-MOVES.png')
 key('z',0.1);time.sleep(0.1);first=shot('01-AFTER-Z.png')
 key('x',0.1);time.sleep(0.1);second=shot('02-AFTER-X.png')
 if ImageChops.difference(initial,first).getbbox() is None:raise RuntimeError('No real move on first input')
 if ImageChops.difference(first,second).getbbox() is None:raise RuntimeError('No changed screen after second input')
finally:
 p.kill();p.wait(timeout=4);d.close()
PYFUSE

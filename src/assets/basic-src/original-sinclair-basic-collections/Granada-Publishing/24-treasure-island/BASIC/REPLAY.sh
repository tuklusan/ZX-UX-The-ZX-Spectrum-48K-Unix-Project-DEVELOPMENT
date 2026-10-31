#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -r "$ROM" && test -r "$HERE/TreasureIsland.tap"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"; cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" SDL_AUDIODRIVER=dummy xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/TreasureIsland.tap" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os,subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import Image,ImageChops
fuse,tape,out=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','250','--auto-load','--tape',tape],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def frame():
 if p.poll() is not None:raise RuntimeError('Fuse stopped')
 wins=d.screen().root.query_tree().children
 w=next((w for w in reversed(wins) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
 if w is None:raise RuntimeError('Fuse display missing')
 w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
 return Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
def key(name,hold=.16):
 sym=XK.string_to_keysym(name);mapping=d.get_keyboard_mapping(8,248)
 kc=next((8+i for i,e in enumerate(mapping) if sym in e),0)
 if not kc:raise RuntimeError('Key missing '+name)
 xtest.fake_input(d,X.KeyPress,kc);d.sync();time.sleep(hold)
 xtest.fake_input(d,X.KeyRelease,kc);d.sync();time.sleep(.2)
def shot(name):
 im=frame();im.save(os.path.join(out,name));return im
try:
 time.sleep(2.5)
 key('r',.12);key('Return',.12)
 time.sleep(3)
 initial=shot('01-MAP.png')
 key('5');time.sleep(1.3);left=shot('02-AFTER-5.png')
 key('8');time.sleep(1.3);right=shot('03-AFTER-8.png')
 key('6');time.sleep(1.3);down=shot('04-AFTER-6.png')
 if ImageChops.difference(initial,left).getbbox() is None:raise RuntimeError('No visible change after first key')
 if ImageChops.difference(left,right).getbbox() is None:raise RuntimeError('No visible change after second key')
 if ImageChops.difference(right,down).getbbox() is None:raise RuntimeError('No visible change after third key')
 print('PASS: original TAP ran in Fuse 48K and changed after documented inputs')
finally:
 p.kill();p.wait(timeout=5);d.close()
PYFUSE

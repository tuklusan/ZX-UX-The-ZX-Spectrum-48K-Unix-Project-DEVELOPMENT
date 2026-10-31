#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -r "$ROM" && test -r "$HERE/SleighRide.tzx"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"; cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" SDL_AUDIODRIVER=dummy xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/SleighRide.tzx" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os,subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import Image,ImageChops
fuse,tape,out=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','250','--auto-load','--tape',tape],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def frame():
 if p.poll() is not None:raise RuntimeError('Fuse exited')
 wins=d.screen().root.query_tree().children
 w=next((w for w in reversed(wins) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
 if w is None:raise RuntimeError('Fuse screen missing')
 w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
 return Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
def key(name,hold=.09):
 sym=XK.string_to_keysym(name);mapping=d.get_keyboard_mapping(8,248)
 kc=next((8+i for i,e in enumerate(mapping) if sym in e),0)
 if not kc:raise RuntimeError('Key missing '+name)
 xtest.fake_input(d,X.KeyPress,kc);d.sync();time.sleep(hold)
 xtest.fake_input(d,X.KeyRelease,kc);d.sync();time.sleep(.20)
def shot(name):
 im=frame();im.save(os.path.join(out,name));return im
try:
 time.sleep(1.6);key('r');key('Return')
 time.sleep(2.8);early=shot('01-SLEIGH-START.png')
 time.sleep(2.8);mid=shot('02-SLEIGH-MOVING.png')
 time.sleep(5.5);later=shot('03-SLEIGH-LATER.png')
 if ImageChops.difference(early,mid).getbbox() is None:raise RuntimeError('No visible animation between first captures')
 if ImageChops.difference(mid,later).getbbox() is None:raise RuntimeError('No later animation change')
 print('PASS: original TZX loaded in Fuse 48K and sleigh animation changed')
finally:
 p.kill();p.wait(timeout=5);d.close()
PYFUSE

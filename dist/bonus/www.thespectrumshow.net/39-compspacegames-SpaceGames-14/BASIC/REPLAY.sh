#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/RESCUE.tzx"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom";cp "$ROM" "$TMP/.spectrum-roms/48.rom"
xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/RESCUE.tzx" "$HERE/SCREENSHOTS" "$TMP" <<'PYFUSE'
import os,subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import Image,ImageChops
fuse,media,out,home=sys.argv[1:]
env=os.environ.copy();env['HOME']=home;env['SDL_AUDIODRIVER']='dummy'
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','400','--auto-load','--tape',media],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def shot(name):
 if p.poll() is not None:raise RuntimeError('Fuse ended')
 w=next((w for w in reversed(d.screen().root.query_tree().children) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
 if w is None:raise RuntimeError('Fuse window absent')
 w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
 im=Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
 im.save(os.path.join(out,name));return im
def key(name,hold=.08):
 sym=XK.string_to_keysym(name)
 mapping=d.get_keyboard_mapping(8,248)
 code=next((8+i for i,v in enumerate(mapping) if sym in v),0)
 if not code:raise RuntimeError('Missing key '+name)
 xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(hold)
 xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.16)
def enter(keys):
 for k in keys:key(k)
try:
 time.sleep(9);key('Return');time.sleep(.5)
 key('r');key('Return');time.sleep(1.2)
 a=shot('01-INSTRUCTIONS-QUESTION.png')
 enter(('n','Return'));time.sleep(.7)
 b=shot('02-ENGINES.png')
 enter(('1','0','0','Return'));time.sleep(.6)
 shot('03-LIFE-SUPPORT.png')
 enter(('1','5','0','Return'));time.sleep(.6)
 shot('04-SHIELDS.png')
 enter(('1','5','0','Return'));time.sleep(2.5)
 c=shot('05-TRIP-EVENT.png')
 if ImageChops.difference(a,b).getbbox() is None:raise RuntimeError('No start after instructions choice')
 if ImageChops.difference(b,c).getbbox() is None:raise RuntimeError('No trip state after energy choices')
 print('PASS: original TZX in Fuse 48K; instructions declined and three energy figures entered')
finally:
 p.kill();p.wait(timeout=5);d.close()
PYFUSE

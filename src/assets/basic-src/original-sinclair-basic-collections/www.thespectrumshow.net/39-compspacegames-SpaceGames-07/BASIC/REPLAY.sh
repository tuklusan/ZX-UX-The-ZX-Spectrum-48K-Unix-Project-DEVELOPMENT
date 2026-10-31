#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/MONSTERS.tzx"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/MONSTERS.tzx" "$HERE/SCREENSHOTS" "$TMP" <<'PYFUSE'
import os,subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import Image, ImageChops
fuse,media,out,home=sys.argv[1:]
env=os.environ.copy();env['HOME']=home;env['SDL_AUDIODRIVER']='dummy'
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','400','--auto-load','--tape',media],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def shot(name):
    if p.poll() is not None:raise RuntimeError('Fuse ended before capture')
    w=next((w for w in reversed(d.screen().root.query_tree().children) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
    if w is None:raise RuntimeError('Fuse screen absent')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    im=Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
    im.save(os.path.join(out,name));return im
def key(name,hold=.08):
    sym=XK.string_to_keysym(name)
    code=d.keysym_to_keycode(sym)
    if not code:raise RuntimeError('Key unavailable: '+name)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.16)
try:
    time.sleep(5)
    key('Return');time.sleep(.5)
    key('r');key('Return');time.sleep(1.2)
    a=shot('01-FIRST-WEAPON.png')
    key('r');key('Return');time.sleep(.35)
    b=shot('02-AFTER-R.png')
    key('s');key('Return');time.sleep(.35)
    c=shot('03-AFTER-S.png')
    if ImageChops.difference(a,b).getbbox() is None:raise RuntimeError('No response after R')
    if ImageChops.difference(b,c).getbbox() is None:raise RuntimeError('No response after S')
    print('PASS: tape loaded in Fuse 48K; R and S choices changed the monster encounter')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

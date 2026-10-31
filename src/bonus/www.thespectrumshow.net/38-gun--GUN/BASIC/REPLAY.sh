#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/GUN.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/GUN.z80" "$HERE/SCREENSHOTS" "$TMP" <<'PYFUSE'
import os,subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import Image,ImageChops
fuse,media,out,home=sys.argv[1:]
env=os.environ.copy();env['HOME']=home;env['SDL_AUDIODRIVER']='dummy'
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','400',media],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def frame():
    if p.poll() is not None:raise RuntimeError('Fuse stopped')
    w=next((v for v in reversed(d.screen().root.query_tree().children) if v.get_geometry().width==320 and v.get_geometry().height==240),None)
    if w is None:raise RuntimeError('Missing Fuse screen')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    return Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
def key(s,hold=.2):
    sym=XK.string_to_keysym(s)
    mapping=d.get_keyboard_mapping(8,248)
    code=next((8+i for i,arr in enumerate(mapping) if sym in arr),0)
    if not code:raise RuntimeError('Missing key '+s)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.2)
def shot(name):
    im=frame();im.save(os.path.join(out,name));return im
def alert(im):
    p=im.crop((43,43,279,64))
    return sum(1 for c in p.get_flattened_data() if min(c)>180)>1500
try:
    time.sleep(2)
    for _ in range(5):
        if not alert(frame()):break
        key('Return',.035);time.sleep(.35)
    editor=shot('01-BASIC-EDITOR.png')
    key('r',.035);key('Return',.035);time.sleep(15)
    instructions=shot('02-INSTRUCTIONS.png')
    if ImageChops.difference(editor,instructions).getbbox() is None:raise RuntimeError('No startup')
    key('space',.3);time.sleep(2)
    choice=shot('03-LEVEL-SELECT.png')
    key('1',.25);time.sleep(2)
    game=shot('04-GAME.png')
    key('5',.5);time.sleep(.3)
    left=shot('05-AFTER-LEFT.png')
    key('8',.5);time.sleep(.3)
    right=shot('06-AFTER-RIGHT.png')
    key('0',.3);time.sleep(.3)
    fired=shot('07-AFTER-FIRE.png')
    if ImageChops.difference(game,left).getbbox() is None:raise RuntimeError('No left key movement')
    if ImageChops.difference(left.crop((30,102,289,114)),right.crop((30,102,289,114))).getbbox() is None:raise RuntimeError('No sight movement on 8')
    if ImageChops.difference(right.crop((30,182,180,202)),fired.crop((30,182,180,202))).getbbox() is None:raise RuntimeError('No ammo change after 0')
    print('PASS: genuine Fuse scene, sight movement, and ammo change after firing')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

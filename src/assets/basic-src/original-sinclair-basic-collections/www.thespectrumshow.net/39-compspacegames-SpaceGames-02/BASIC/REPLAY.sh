#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/INTGAMES.tzx"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom";cp "$ROM" "$TMP/.spectrum-roms/48.rom"
xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/INTGAMES.tzx" "$HERE/SCREENSHOTS" "$TMP" <<'PYFUSE'
import os,subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import Image,ImageChops
fuse,media,out,home=sys.argv[1:]
env=os.environ.copy();env['HOME']=home;env['SDL_AUDIODRIVER']='dummy'
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','400','--auto-load','--tape',media],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def frame():
    if p.poll() is not None:raise RuntimeError('Fuse stopped')
    w=next((w for w in reversed(d.screen().root.query_tree().children) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
    if w is None:raise RuntimeError('Fuse screen missing')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    return Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
def key(s,hold=.06):
    mapping=d.get_keyboard_mapping(8,248)
    sym=XK.string_to_keysym(s)
    code=next((8+i for i,entry in enumerate(mapping) if sym in entry),0)
    if not code:raise RuntimeError('Key missing '+s)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.18)
def shot(name):
    im=frame();im.save(os.path.join(out,name));return im
try:
    time.sleep(5)
    for _ in range(5):
        im=frame();region=im.crop((43,43,279,64))
        if sum(1 for pix in region.get_flattened_data() if min(pix)>180)<1500:break
        key('Return',.035);time.sleep(.3)
    listing=shot('01-LOADED-BASIC.png')
    key('r',.035);key('Return',.035);time.sleep(2)
    first=shot('02-ANGLE-PROMPT.png')
    for k in ('4','5','Return'):key(k,.035)
    time.sleep(.7);second=shot('03-SPEED-PROMPT.png')
    for k in ('1','2','0','0','0','Return'):key(k,.035)
    time.sleep(.7);third=shot('04-AFTER-LAUNCH.png')
    if ImageChops.difference(listing,first).getbbox() is None:raise RuntimeError('No program started')
    if ImageChops.difference(first,second).getbbox() is None:raise RuntimeError('No speed prompt after angle')
    if ImageChops.difference(second,third).getbbox() is None:raise RuntimeError('No result after speed')
    print('PASS: original TZX loaded in Fuse; angle and speed entries changed program screens')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

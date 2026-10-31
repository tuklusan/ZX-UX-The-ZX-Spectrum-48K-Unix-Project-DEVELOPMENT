#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/ROBOT-FINAL.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/ROBOT-FINAL.z80" "$HERE/SCREENSHOTS" "$TMP" <<'PYFUSE'
import os,sys,subprocess,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import Image,ImageChops
fuse,media,out,home=sys.argv[1:]
env=os.environ.copy();env['HOME']=home;env['SDL_AUDIODRIVER']='dummy'
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','400','--snapshot',media],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def frame():
    if p.poll() is not None:raise RuntimeError('Fuse ended')
    w=next((w for w in reversed(d.screen().root.query_tree().children) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
    if w is None:raise RuntimeError('Fuse screen missing')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    return Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
def key(s,hold=.04,wait=.18):
    sym=XK.string_to_keysym(s)
    mapping=d.get_keyboard_mapping(8,248)
    code=next((8+i for i,entry in enumerate(mapping) if sym in entry),0)
    if not code:raise RuntimeError('Missing key '+s)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(wait)
def shot(name):
    im=frame();im.save(os.path.join(out,name));return im
try:
    time.sleep(2)
    key('r');key('Return');time.sleep(1.1)
    key('Return');time.sleep(1.1)
    intro=shot('01-LEVEL.png')
    key('1');time.sleep(1.1)
    key('0');time.sleep(1.1)
    key('Return');time.sleep(.7)
    key('Return');time.sleep(.15)
    game=shot('02-GAME.png')
    if sum(1 for px in game.get_flattened_data() if px==(0,194,0))<100:
        raise RuntimeError('Active Robot Chase board not visible')
    previous=game
    for name,s in [('03-AFTER-F.png','f'),('04-AFTER-G.png','g'),('05-AFTER-V.png','v'),('06-AFTER-T.png','t')]:
        key(s,wait=.07)
        current=shot(name)
        if ImageChops.difference(previous,current).getbbox() is None:
            raise RuntimeError('Screen unchanged after '+s)
        previous=current
    print('PASS: original snapshot started Robot Chase; four documented keys and active game images recorded')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

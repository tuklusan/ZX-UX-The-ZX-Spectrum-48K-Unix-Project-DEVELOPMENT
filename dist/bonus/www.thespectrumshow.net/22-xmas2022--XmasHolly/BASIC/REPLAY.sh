#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/XmasHolly.tzx"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/XmasHolly.tzx" "$HERE/SCREENSHOTS" "$TMP" <<'PYFUSE'
import os,sys,subprocess,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import Image,ImageChops
fuse,media,out,home=sys.argv[1:]
env=os.environ.copy();env['HOME']=home;env['SDL_AUDIODRIVER']='dummy'
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','400','--auto-load','--tape',media],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def frame():
    if p.poll() is not None:raise RuntimeError('Fuse exited')
    w=next((w for w in reversed(d.screen().root.query_tree().children) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
    if w is None:raise RuntimeError('Fuse screen missing')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    return Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
def key(s):
    mapping=d.get_keyboard_mapping(8,248)
    sym=XK.string_to_keysym(s)
    code=next((8+i for i,entry in enumerate(mapping) if sym in entry),0)
    if not code:raise RuntimeError('Missing key '+s)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(.04)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.18)
def shot(name):
    im=frame();im.save(os.path.join(out,name));return im
try:
    time.sleep(6)
    loaded=shot('01-LOADED.png')
    key('r');key('Return');time.sleep(1)
    early=shot('02-EARLY-HOLLY.png')
    time.sleep(9)
    later=shot('03-MORE-HOLLY.png')
    if ImageChops.difference(loaded,early).getbbox() is None:raise RuntimeError('No drawing after RUN')
    if ImageChops.difference(early,later).getbbox() is None:raise RuntimeError('No growth between holly images')
    if sum(1 for pix in later.get_flattened_data() if pix[1]>pix[0]*1.8 and pix[1]>pix[2]*1.8)<50:
        raise RuntimeError('Green holly drawing not present')
    print('PASS: original tape loaded; RUN produced growing holly drawing in Fuse')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

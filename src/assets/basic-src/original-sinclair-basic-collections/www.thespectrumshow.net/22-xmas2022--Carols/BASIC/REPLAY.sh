#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/Carols.tzx"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/Carols.tzx" "$HERE/SCREENSHOTS" "$TMP" <<'PYFUSE'
import os,sys,subprocess,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import Image,ImageChops
fuse,media,out,home=sys.argv[1:]
env=os.environ.copy();env['HOME']=home;env['SDL_AUDIODRIVER']='dummy'
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','400','--auto-load','--tape',media],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def frame():
    if p.poll() is not None:raise RuntimeError('Fuse ended')
    w=next((w for w in reversed(d.screen().root.query_tree().children) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
    if w is None:raise RuntimeError('Fuse window not found')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    return Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
def key(s):
    mapping=d.get_keyboard_mapping(8,248)
    sym=XK.string_to_keysym(s)
    code=next((8+i for i,v in enumerate(mapping) if sym in v),0)
    if not code:raise RuntimeError('Missing key '+s)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(.05)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.15)
def shot(name):
    im=frame();im.save(os.path.join(out,name));return im
try:
    time.sleep(6)
    key('r');key('Return');time.sleep(2)
    prompt=shot('01-START-PROMPT.png')
    key('space');time.sleep(1)
    song=shot('02-FIRST-CAROL.png')
    if ImageChops.difference(prompt,song).getbbox() is None:
        raise RuntimeError('No response to start key')
    time.sleep(5)
    still=shot('03-FIVE-SECONDS-LATER.png')
    print('PASS: original tape reached start prompt and first carol screen in Fuse; audio disabled')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

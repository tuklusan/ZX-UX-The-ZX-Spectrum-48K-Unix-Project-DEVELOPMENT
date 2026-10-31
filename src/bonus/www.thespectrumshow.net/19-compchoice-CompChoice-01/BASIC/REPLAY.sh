#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/List1.tzx"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$TMP/.fuse" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
cp "$ROM" "$TMP/.fuse/48.rom"
HOME="$TMP" SDL_AUDIODRIVER=dummy xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/List1.tzx" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os,sys,subprocess,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import Image,ImageChops
fuse,media,out=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','400','--auto-load','--tape',media],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def frame():
    if p.poll() is not None:raise RuntimeError('Fuse ended')
    w=next((w for w in reversed(d.screen().root.query_tree().children) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
    if w is None:raise RuntimeError('No Fuse picture')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    return Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
def shot(name):
    im=frame();im.save(os.path.join(out,name));return im
def key(s):
    sym=XK.string_to_keysym(s)
    mapping=d.get_keyboard_mapping(8,248)
    code=next((8+i for i,entry in enumerate(mapping) if sym in entry),0)
    if not code:raise RuntimeError('Missing key '+s)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(.04)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.2)
try:
    time.sleep(4)
    key('Return');time.sleep(.7)
    loaded=shot('01-LISTING.png')
    key('r');key('Return');time.sleep(.6)
    running=shot('02-RUN.png')
    time.sleep(6)
    stopped=shot('03-STOP.png')
    if ImageChops.difference(loaded,running).getbbox() is None:raise RuntimeError('No change after RUN')
    if ImageChops.difference(running,stopped).getbbox() is None:raise RuntimeError('No changed screen by STOP')
    print('PASS: original list ran in Fuse 48K and reached its STOP line')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

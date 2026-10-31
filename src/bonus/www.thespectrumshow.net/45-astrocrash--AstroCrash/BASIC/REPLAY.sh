#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/AstroCrash.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$TMP/.fuse" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
cp "$ROM" "$TMP/.fuse/48.rom"
HOME="$TMP" SDL_AUDIODRIVER=dummy xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/AstroCrash.z80" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os,subprocess,time,sys
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import Image,ImageChops
fuse,media,out=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','150','--snapshot',media],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def frame():
    if p.poll() is not None:raise RuntimeError('Fuse ended')
    w=next((w for w in reversed(d.screen().root.query_tree().children) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
    if w is None:raise RuntimeError('Fuse game screen missing')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    return Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
def key(s,hold=.08):
    sym=XK.string_to_keysym(s)
    mapping=d.get_keyboard_mapping(8,248)
    code=next((8+i for i,entry in enumerate(mapping) if sym in entry),0)
    if not code:raise RuntimeError('Key missing '+s)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.15)
def shot(name):
    im=frame();im.save(os.path.join(out,name));return im
try:
    time.sleep(.7)
    key('Return');time.sleep(.4)
    controls=shot('01-CONTROLS.png')
    key('y');key('Return');time.sleep(.7)
    a=shot('02-GAME.png')
    key('x');time.sleep(.1);b=shot('03-AFTER-X.png')
    key('space');time.sleep(.1);c=shot('04-AFTER-SPACE.png')
    key('Return');time.sleep(.1);dimage=shot('05-AFTER-FIRE.png')
    key('z');time.sleep(.1);e=shot('06-AFTER-Z.png')
    if ImageChops.difference(controls,a).getbbox() is None:raise RuntimeError('No game launch')
    if ImageChops.difference(a,b).getbbox() is None:raise RuntimeError('No live screen change after X')
    if ImageChops.difference(b,c).getbbox() is None:raise RuntimeError('No live screen change after Space')
    if ImageChops.difference(c,dimage).getbbox() is None:raise RuntimeError('No live screen change after fire')
    print('PASS: original snapshot started in Fuse 48K; live gameplay and actions recorded')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/MOONLAND.tzx"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/MOONLAND.tzx" "$HERE/SCREENSHOTS" "$TMP" <<'PYFUSE'
import os,subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import Image
fuse,media,out,home=sys.argv[1:]
env=os.environ.copy();env['HOME']=home;env['SDL_AUDIODRIVER']='dummy'
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','50','--auto-load','--tape',media],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def frame():
    if p.poll() is not None:raise RuntimeError('Fuse ended early')
    w=next((w for w in reversed(d.screen().root.query_tree().children)
            if w.get_geometry().width==320 and w.get_geometry().height==240),None)
    if w is None:raise RuntimeError('Fuse screen missing')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    return Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
def key(s,hold=.08):
    mapping=d.get_keyboard_mapping(8,248)
    sym=XK.string_to_keysym(s)
    code=next((8+i for i,entry in enumerate(mapping) if sym in entry),0)
    if not code:raise RuntimeError('Missing key '+s)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.07)
try:
    time.sleep(5)
    key('Return');time.sleep(.8)
    key('r');key('Return');time.sleep(1.4)
    before=frame();before.save(out+'/01-BURN-PROMPT.png')
    for k in ('0','Return'):key(k)
    time.sleep(.4);first=frame();first.save(out+'/02-AFTER-ZERO-BURN.png')
    for k in ('3','0','Return'):key(k)
    time.sleep(.4);second=frame();second.save(out+'/03-AFTER-THIRTY-BURN.png')
    from PIL import ImageChops
    if ImageChops.difference(before,first).getbbox() is None:
        raise RuntimeError('No view change after first input')
    if ImageChops.difference(first,second).getbbox() is None:
        raise RuntimeError('No view change after second input')
    print('PASS: original Moonlander tape in Fuse; two burn values entered')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

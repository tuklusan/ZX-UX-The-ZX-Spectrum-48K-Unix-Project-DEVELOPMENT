#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/BUG.tzx"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/BUG.tzx" "$HERE/SCREENSHOTS" "$TMP" <<'PYFUSE'
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
def black(im):
    return sum(max(px)<75 for px in im.crop((0,0,320,220)).get_flattened_data())
try:
    time.sleep(5)
    key('Return');time.sleep(.8)
    key('r');key('Return')
    eyes=False;after=False;blast=False;sent=0
    start=time.monotonic();next_key=start+.5
    while time.monotonic()-start < 45:
        im=frame();count=black(im)
        if 27<=count<=38 and not eyes:
            im.save(out+'/01-EYES.png');eyes=True
        if 27<=count<=38 and sent>=2 and not after:
            im.save(out+'/02-AFTER-TWO-KEYS.png');after=True
        if 8<=count<=18 and sent>=2 and not blast:
            im.save(out+'/03-HIT.png');blast=True
        if eyes and after and blast:break
        if eyes and time.monotonic()>=next_key:
            key(('1','4','2','3')[sent%4],.12)
            sent+=1;next_key=time.monotonic()+.22
        else:time.sleep(.045)
    if not eyes:raise RuntimeError('No live bug-eye frame')
    if sent<2 or not after:raise RuntimeError('Two input attempts not observed in running game')
    if not blast:raise RuntimeError('No hit screen seen after number-key input')
    print('PASS: original BUG tape loaded in Fuse; numbered keys used; eyes and hit shown')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

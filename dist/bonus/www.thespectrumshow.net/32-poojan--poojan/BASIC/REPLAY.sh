#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/poojan.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/poojan.z80" "$HERE/SCREENSHOTS" "$TMP" <<'PYFUSE'
import os, subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import Image, ImageChops
fuse, media, out, home=sys.argv[1:]
env=os.environ.copy();env['HOME']=home;env['SDL_AUDIODRIVER']='dummy'
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','400',media],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def frame():
    if p.poll() is not None:raise RuntimeError('Fuse stopped')
    wins=d.screen().root.query_tree().children
    w=next((w for w in reversed(wins) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
    if w is None:raise RuntimeError('Fuse screen missing')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    g=w.get_geometry();raw=w.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff)
    return Image.frombytes('RGB',(g.width,g.height),raw.data,'raw','BGRX')
def key(s,hold=.22):
    sym=XK.string_to_keysym(s)
    mapping=d.get_keyboard_mapping(8,248)
    code=next((8+i for i,entry in enumerate(mapping) if sym in entry),0)
    if not code:raise RuntimeError('Missing key '+s)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.2)
def dialog(im):
    region=im.crop((43,43,279,64))
    return sum(1 for r,g,b in region.get_flattened_data() if min(r,g,b)>180)>1500
def cyan(im):
    return sum(1 for y in range(20,63) for x in range(30,300) if im.getpixel((x,y))[0]<110 and min(im.getpixel((x,y))[1:])>155)
def actor_y(im):
    ys=[]
    for y in range(55,210):
        for x in range(214,232):
            r,g,b=im.getpixel((x,y))
            if r>160 and g>160 and b<115:ys.append(y)
    return sum(ys)/len(ys) if len(ys)>5 else None
try:
    time.sleep(2.5)
    for _ in range(5):
        if not dialog(frame()):break
        key('Return',.1);time.sleep(.3)
    time.sleep(20)
    intro=frame();intro.save(os.path.join(out,'01-HALL-OF-FAME.png'))
    if cyan(intro)>10:raise RuntimeError('Wrong starting screen')
    key('space',.1);time.sleep(5)
    game=frame();game.save(os.path.join(out,'02-GAME.png'))
    key('z',.4)
    down=frame();down.save(os.path.join(out,'03-AFTER-DOWN.png'))
    key('a',.4)
    up=frame();up.save(os.path.join(out,'04-AFTER-UP.png'))
    key('space',.3)
    fire=frame();fire.save(os.path.join(out,'05-AFTER-FIRE.png'))
    if cyan(game)<15:raise RuntimeError('Game view not confirmed')
    positions=[actor_y(x) for x in (game,down,up)]
    if any(x is None for x in positions):raise RuntimeError('Actor not visible: '+str(positions))
    if not (positions[1]>positions[0]+8 and positions[2]<positions[1]-8):
        raise RuntimeError('Vertical movement not confirmed: '+str(positions))
    if ImageChops.difference(up,fire).getbbox() is None:raise RuntimeError('No fire screen change')
    print('PASS: live Poojan gameplay; down and up controls; screen change after fire',positions)
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

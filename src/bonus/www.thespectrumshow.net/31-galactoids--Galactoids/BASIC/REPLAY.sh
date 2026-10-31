#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/Galactoids.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/Galactoids.z80" "$HERE/SCREENSHOTS" "$TMP" <<'PYFUSE'
import os, subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import Image, ImageChops
fuse, media, out, home = sys.argv[1:]
env=os.environ.copy();env['HOME']=home;env['SDL_AUDIODRIVER']='dummy'
p=subprocess.Popen([fuse,'--no-sound','--machine','48',media],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def window():
    wins=d.screen().root.query_tree().children
    w=next((w for w in reversed(wins) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
    if w is None:raise RuntimeError('Fuse window unavailable')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    return w
def frame():
    if p.poll() is not None:raise RuntimeError('Fuse stopped')
    w=window();g=w.get_geometry()
    raw=w.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff)
    return Image.frombytes('RGB',(g.width,g.height),raw.data,'raw','BGRX')
def key(s,hold=.3):
    sym=XK.string_to_keysym(s)
    mapping=d.get_keyboard_mapping(8,248)
    code=next((8+i for i,entry in enumerate(mapping) if sym in entry),0)
    if not code:raise RuntimeError('Missing key '+s)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.25)
def boot_dialog(im):
    region=im.crop((43,43,279,64))
    bright=sum(1 for r,g,b in region.get_flattened_data() if min(r,g,b)>180)
    return bright>1500
def player_x(im):
    points=[]
    for y in range(192,201):
        for x in range(45,277):
            r,g,b=im.getpixel((x,y))
            if min(r,g,b)>180:points.append(x)
    if len(points)<6:return None
    return sum(points)/len(points)
try:
    time.sleep(2.5)
    for _ in range(5):
        now=frame()
        if not boot_dialog(now):break
        key('Return',.1)
        time.sleep(.5)
    time.sleep(.5)
    intro=frame()
    if boot_dialog(intro):raise RuntimeError('Fuse startup message still on screen')
    intro.save(os.path.join(out,'01-INSTRUCTIONS.png'))
    key('Return',.1)
    time.sleep(.7)
    start=frame();start.save(os.path.join(out,'02-GAME.png'))
    if ImageChops.difference(intro,start).getbbox() is None:raise RuntimeError('Start did not change screen')
    key('z',.4)
    left=frame();left.save(os.path.join(out,'03-AFTER-LEFT.png'))
    key('x',.8)
    right=frame();right.save(os.path.join(out,'04-AFTER-RIGHT.png'))
    key('space',.4)
    firing=frame();firing.save(os.path.join(out,'05-AFTER-FIRE.png'))
    positions=[player_x(x) for x in (left,right)]
    if None in positions or positions[1]-positions[0]<25:
        raise RuntimeError('Player motion not proved: '+str(positions))
    if ImageChops.difference(right,firing).getbbox() is None:
        raise RuntimeError('No visible change after fire')
    print('PASS: game starts; player moves left and right; firing changes view; player positions',positions)
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

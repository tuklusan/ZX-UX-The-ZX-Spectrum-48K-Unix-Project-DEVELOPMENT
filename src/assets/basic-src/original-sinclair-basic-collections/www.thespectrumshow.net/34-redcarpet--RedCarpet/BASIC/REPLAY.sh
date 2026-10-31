#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/RedCarpet.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/RedCarpet.z80" "$HERE/SCREENSHOTS" "$TMP" <<'PYFUSE'
import os,subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import Image,ImageChops
fuse,media,out,home=sys.argv[1:]
env=os.environ.copy();env['HOME']=home;env['SDL_AUDIODRIVER']='dummy'
p=subprocess.Popen([fuse,'--no-sound','--machine','48',media],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def frame():
    if p.poll() is not None:raise RuntimeError('Fuse stopped')
    wins=d.screen().root.query_tree().children
    w=next((w for w in reversed(wins) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
    if w is None:raise RuntimeError('Fuse screen missing')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    g=w.get_geometry();r=w.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff)
    return Image.frombytes('RGB',(g.width,g.height),r.data,'raw','BGRX')
def key(s,hold=.15):
    sym=XK.string_to_keysym(s)
    mapping=d.get_keyboard_mapping(8,248)
    code=next((8+i for i,entry in enumerate(mapping) if sym in entry),0)
    if not code:raise RuntimeError('Missing key '+s)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.12)
def dialog(im):
    region=im.crop((43,43,279,64))
    return sum(1 for r,g,b in region.get_flattened_data() if min(r,g,b)>180)>1500
def player_position(im):
    points=[]
    for y in range(48,189):
        for x in range(48,276):
            r,g,b=im.getpixel((x,y))
            if min(r,g,b)>170:points.append((x,y))
    return (sum(x for x,y in points)/len(points),sum(y for x,y in points)/len(points)) if len(points)>1 else None
try:
    time.sleep(2.5)
    for _ in range(5):
        if not dialog(frame()):break
        key('Return',.1);time.sleep(1.0)
    stop=frame();stop.save(os.path.join(out,'01-STOP-TAPE.png'))
    key('space',.2)
    time.sleep(.7)
    controls=frame();controls.save(os.path.join(out,'02-CONTROLS.png'))
    key('s',.6)
    time.sleep(.7)
    game=frame();game.save(os.path.join(out,'03-GAME.png'))
    key('f',.18)
    up=frame();up.save(os.path.join(out,'04-AFTER-UP.png'))
    key('z',.18)
    left=frame();left.save(os.path.join(out,'05-AFTER-LEFT.png'))
    positions=[player_position(x) for x in (game,up,left)]
    if any(x is None for x in positions) or not (positions[1][1]<positions[0][1]-3 and positions[2][0]<positions[1][0]-3):
        raise RuntimeError('Movement not confirmed: '+str(positions))
    if ImageChops.difference(controls,game).getbbox() is None:raise RuntimeError('Game did not start')
    print('PASS: maze play started; F moved up and Z moved left',positions)
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

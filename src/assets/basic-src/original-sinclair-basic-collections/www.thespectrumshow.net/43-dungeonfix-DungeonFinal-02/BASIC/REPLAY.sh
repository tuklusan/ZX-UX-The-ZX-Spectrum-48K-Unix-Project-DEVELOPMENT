#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/DUNGEON.tzx"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom";cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" SDL_AUDIODRIVER=dummy xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/DUNGEON.tzx" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os, subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import Image, ImageChops
fuse,media,out=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','400','--auto-load','--tape',media],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def window():
    if p.poll() is not None: raise RuntimeError('Fuse exited')
    w=next((w for w in reversed(d.screen().root.query_tree().children) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
    if w is None: raise RuntimeError('Fuse screen missing')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();return w
def key(s,hold=.10):
    sym=XK.string_to_keysym(s)
    mapping=d.get_keyboard_mapping(8,248)
    keynum=next((8+i for i,row in enumerate(mapping) if sym in row),0)
    if not keynum: raise RuntimeError('Unmapped key '+s)
    window();xtest.fake_input(d,X.KeyPress,keynum);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,keynum);d.sync()
def shot(name):
    w=window();im=Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
    im.save(os.path.join(out,name));return im
try:
    time.sleep(6);key('n',.13);key('Return',.13)
    time.sleep(17);key('c',.035);time.sleep(.5);key('BackSpace',.10);time.sleep(.25)
    for k in ('1','Return'):key(k,.035)
    time.sleep(.5)
    for k in ('1','Return'):key(k,.035)
    time.sleep(2)
    first=shot('01-MAP-START.png')
    key('e',.10);time.sleep(.65);east=shot('02-AFTER-EAST.png')
    key('s',.10);time.sleep(.65);south=shot('03-AFTER-SOUTH.png')
    key('w',.10);time.sleep(.65);west=shot('04-AFTER-WEST.png')
    if ImageChops.difference(first,east).getbbox() is None: raise RuntimeError('No game response to east input')
    if ImageChops.difference(east,south).getbbox() is None: raise RuntimeError('No change after south input')
    print('PASS: original two-part tape, stats, equipment, map and player inputs in Fuse')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

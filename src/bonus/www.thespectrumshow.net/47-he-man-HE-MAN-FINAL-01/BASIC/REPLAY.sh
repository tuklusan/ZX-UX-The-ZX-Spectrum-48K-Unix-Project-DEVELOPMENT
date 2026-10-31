#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/HE-MAN.tzx"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" SDL_AUDIODRIVER=dummy xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/HE-MAN.tzx" "$HERE/SCREENSHOTS" <<'PYFUSE'
import os, subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import Image, ImageChops
fuse, media, out = sys.argv[1:]
p = subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','200','--auto-load','--tape',media],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d = display.Display()
def window():
    if p.poll() is not None: raise RuntimeError('Fuse exited')
    w=next((w for w in reversed(d.screen().root.query_tree().children) if w.get_geometry().width==320 and w.get_geometry().height==240),None)
    if w is None: raise RuntimeError('Fuse window missing')
    w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    return w
def key(name, hold=.07):
    symbol=XK.string_to_keysym(name)
    mapping=d.get_keyboard_mapping(8,248)
    number=next((8+i for i,row in enumerate(mapping) if symbol in row),0)
    if not number: raise RuntimeError('Key missing '+name)
    window();xtest.fake_input(d,X.KeyPress,number);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,number);d.sync()
def shot(name):
    w=window();frame=Image.frombytes('RGB',(320,240),w.get_image(0,0,320,240,X.ZPixmap,0xffffffff).data,'raw','BGRX')
    frame.save(os.path.join(out,name));return frame
try:
    time.sleep(7)
    first=shot('01-QUEST-INSTRUCTIONS.png')
    key('space');time.sleep(.8)
    second=shot('02-STATUS-BEFORE-BATTLE.png')
    key('space');time.sleep(.8)
    third=shot('03-AFTER-FIRST-KEY.png')
    key('space');time.sleep(.8)
    fourth=shot('04-AFTER-SECOND-KEY.png')
    for x,y in ((first,second),(second,third),(third,fourth)):
        if ImageChops.difference(x,y).getbbox() is None: raise RuntimeError('No visible game change after input')
    print('PASS: original BASIC and CODE tape, three Fuse key actions')
finally:
    p.kill();p.wait(timeout=5);d.close()
PYFUSE

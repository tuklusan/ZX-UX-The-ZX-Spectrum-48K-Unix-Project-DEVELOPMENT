#!/bin/sh
# SANYALnet Labs: original 48K snapshot replay with real keyboard input.
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/Amaze.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/Amaze.z80" "$HERE/SCREENSHOTS" <<'PYFUSE'
import subprocess,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import ImageGrab,ImageChops
fuse,snapshot,output=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','100','--snapshot',snapshot],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def key(name,hold):
    sym=XK.string_to_keysym(name)
    code=d.keysym_to_keycode(sym)
    if not code: raise RuntimeError('Unmapped key: '+name)
    xtest.fake_input(d,X.KeyPress,code);d.sync();time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,code);d.sync();time.sleep(.35)
def shot(name):
    if p.poll() is not None: raise RuntimeError('Fuse exited')
    image=ImageGrab.grab().crop((240,180,560,420))
    image.save(output+'/'+name)
    return image
try:
    time.sleep(2.0)
    # The archived snapshot resumes on GAME OVER; Enter restarts the BASIC maze.
    key('Return',.15)
    time.sleep(13.0)
    start=shot('01-MAZE.png')
    key('5',.18)
    time.sleep(.4)
    moved=shot('02-AFTER-5.png')
    key('8',.18)
    time.sleep(.4)
    after=shot('03-AFTER-8.png')
    if not ImageChops.difference(start,moved).getbbox() or not ImageChops.difference(moved,after).getbbox():
        raise RuntimeError('No visible screen change after controls')
finally:
    p.kill();p.wait(timeout=4);d.close()
PYFUSE

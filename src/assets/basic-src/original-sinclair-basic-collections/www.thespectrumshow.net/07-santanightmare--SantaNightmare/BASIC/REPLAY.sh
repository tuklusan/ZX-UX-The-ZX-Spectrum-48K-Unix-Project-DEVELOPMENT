#!/bin/sh
# Real 48K Fuse keyboard replay against original SantaNightmare.z80, no image substitution.
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/SantaNightmare.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/SantaNightmare.z80" "$HERE/SCREENSHOTS" <<'PY'
import subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import ImageGrab, ImageChops
fuse,snapshot,output=sys.argv[1:]
p=subprocess.Popen([fuse,'--no-sound','--machine','48','--speed','100','--snapshot',snapshot],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d=display.Display()
def key(name,hold=.2):
    c=d.keysym_to_keycode(XK.string_to_keysym(name))
    if not c: raise RuntimeError('Unmapped key '+name)
    xtest.fake_input(d,X.KeyPress,c); d.sync(); time.sleep(hold)
    xtest.fake_input(d,X.KeyRelease,c); d.sync()
def screen():
    if p.poll() is not None: raise RuntimeError('Fuse exited before gameplay')
    return ImageGrab.grab().crop((240,180,560,420))
try:
    time.sleep(1.5)
    initial=screen()
    
    # Read all three instructions pages (BASIC 9210-9270).
    for _ in range(3): key('space'); time.sleep(.55)
    # Define four distinct controls on the setup screen (BASIC 60-100).
    for chosen in ('a','d','w','s'): key(chosen); time.sleep(.65)
    # Wait for the 1985 stage 1 reminder, then continue (BASIC 9300-9710).
    time.sleep(4.0)
    # Press to leave the reminder; ignore the countdown until stage 1 appears.
    for _ in range(30):
        key('space',.35); time.sleep(.65)
        preview=screen().convert('RGB')
        if sum(1 for rgb in preview.getdata() if rgb == (0,194,0)) >= 180:
            break
    else:
        raise RuntimeError('The first playable stage never appeared')
    before=screen()
    key('a',.6); time.sleep(.35)
    first=screen()
    if not ImageChops.difference(before,first).getbbox(): raise RuntimeError('First move had no visible effect')
    first.save(output+'/01-STATE.png')
    key('d',.6); time.sleep(.35)
    second=screen()
    if not ImageChops.difference(first,second).getbbox(): raise RuntimeError('Second move had no visible effect')
    second.save(output+'/02-AFTER-MOVES.png')
finally:
    p.kill(); p.wait(timeout=4); d.close()
PY

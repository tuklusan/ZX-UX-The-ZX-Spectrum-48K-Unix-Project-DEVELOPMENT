#!/bin/sh
# Real 48K Fuse keyboard replay against original beltman.z80, no image substitution.
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/beltman.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/beltman.z80" "$HERE/SCREENSHOTS" <<'PY'
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
    time.sleep(.4)
    before=screen()
    key('8',.8); time.sleep(.25)
    first=screen()
    if not ImageChops.difference(before,first).getbbox(): raise RuntimeError('First move had no visible effect')
    first.save(output+'/01-STATE.png')
    key('6',.8); time.sleep(.25)
    second=screen()
    if not ImageChops.difference(first,second).getbbox(): raise RuntimeError('Second move had no visible effect')
    second.save(output+'/02-AFTER-MOVES.png')
finally:
    p.kill(); p.wait(timeout=4); d.close()
PY

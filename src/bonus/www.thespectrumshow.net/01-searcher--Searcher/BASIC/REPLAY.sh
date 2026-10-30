#!/bin/sh
# Replay actual keyboard controls from Searcher BASIC lines 90-132 and 8020-8029.
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/Searcher.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.spectrum-roms/48.rom"
HOME="$TMP" xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/Searcher.z80" "$HERE/SCREENSHOTS" <<'PY'
import subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import ImageGrab, ImageChops
fuse, snapshot, output = sys.argv[1:]
p = subprocess.Popen([fuse, '--no-sound','--machine','48','--speed','100','--snapshot',snapshot], stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
d = display.Display()
def key(name, hold=0.2):
    code=d.keysym_to_keycode(XK.string_to_keysym(name))
    if not code: raise RuntimeError('Key not mapped: '+name)
    xtest.fake_input(d, X.KeyPress, code); d.sync(); time.sleep(hold)
    xtest.fake_input(d, X.KeyRelease, code); d.sync()
def screen():
    if p.poll() is not None: raise RuntimeError('Fuse exited early')
    return ImageGrab.grab().crop((240,180,560,420))
try:
    time.sleep(1.8)
    intro=screen()
    key('Return')                 # BASIC 8029: PRESS ENTER TO START
    time.sleep(1.0)
    initial=screen()
    if not ImageChops.difference(intro,initial).getbbox(): raise RuntimeError('ENTER did not leave the instructions')
    key('7',0.25)                 # BASIC 120: UP
    time.sleep(0.35)
    key('8',0.25)                 # BASIC 122: FORWARD
    time.sleep(0.3)
    played=screen()
    if not ImageChops.difference(initial,played).getbbox(): raise RuntimeError('Movement did not change screen')
    played.save(output+'/01-STATE.png')
    key('9',0.3)                  # BASIC 130: FIRE
    time.sleep(0.35)
    key('6',0.3)                  # BASIC 121: DOWN
    time.sleep(0.3)
    moved=screen()
    if not ImageChops.difference(played,moved).getbbox(): raise RuntimeError('Further gameplay did not change screen')
    moved.save(output+'/02-AFTER-FIRE-AND-DOWN.png')
finally:
    p.kill()
    p.wait(timeout=4)
    d.close()
PY

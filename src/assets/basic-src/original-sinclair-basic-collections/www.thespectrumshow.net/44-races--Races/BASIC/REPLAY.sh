#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../../../.." && pwd)
ROM=${ZX_ROM_48:-$ROOT/src/zx-ux-sdk/rom/48.rom}
FUSE=${FUSE_BIN:-fuse-sdl}
test -f "$ROM" && test -f "$HERE/races.z80"
command -v "$FUSE" >/dev/null
command -v xvfb-run >/dev/null
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP/.fuse" "$TMP/.spectrum-roms" "$HERE/SCREENSHOTS"
cp "$ROM" "$TMP/.fuse/48.rom"; cp "$ROM" "$TMP/.spectrum-roms/48.rom"
xvfb-run -a -s '-screen 0 800x600x24' python3 - "$FUSE" "$HERE/races.z80" "$HERE/SCREENSHOTS" "$TMP" <<'PYFUSE'
import os, subprocess, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import Image, ImageChops
fuse, media, out, home = sys.argv[1:]
env = os.environ.copy(); env['HOME'] = home; env['SDL_AUDIODRIVER'] = 'dummy'
p = subprocess.Popen([fuse, '--no-sound', '--machine', '48', '--speed', '300', '--snapshot', media], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
d = display.Display()
def shot(name):
    if p.poll() is not None: raise RuntimeError('Fuse stopped')
    w = next((w for w in reversed(d.screen().root.query_tree().children) if w.get_geometry().width == 320 and w.get_geometry().height == 240), None)
    if w is None: raise RuntimeError('No Fuse window')
    w.set_input_focus(X.RevertToParent, X.CurrentTime); d.sync()
    im = Image.frombytes('RGB', (320, 240), w.get_image(0, 0, 320, 240, X.ZPixmap, 0xffffffff).data, 'raw', 'BGRX')
    im.save(os.path.join(out, name)); return im
def key(s, hold=.14):
    sym = XK.string_to_keysym(s)
    mapping = d.get_keyboard_mapping(8, 248)
    code = next((8+i for i,v in enumerate(mapping) if sym in v), 0)
    if not code: raise RuntimeError('Missing key '+s)
    xtest.fake_input(d, X.KeyPress, code); d.sync(); time.sleep(hold)
    xtest.fake_input(d, X.KeyRelease, code); d.sync(); time.sleep(.23)
try:
    time.sleep(2)
    shot('00-TITLE.png')
    key('Return'); time.sleep(1.3)
    key('y'); time.sleep(1.3)
    a = shot('01-HORSE-CHOICE.png')
    key('1'); time.sleep(1.3)
    b = shot('02-STAKE-PROMPT.png')
    key('2'); time.sleep(.1)
    key('Return'); time.sleep(1.3)
    c = shot('03-RACE-STARTED.png')
    if ImageChops.difference(a,b).getbbox() is None: raise RuntimeError('No horse chosen')
    if ImageChops.difference(b,c).getbbox() is None: raise RuntimeError('No race after wager')
    print('PASS: original 48K snapshot; selected horse 1, wagered 2, reached moving race')
finally:
    p.kill(); p.wait(timeout=5); d.close()
PYFUSE

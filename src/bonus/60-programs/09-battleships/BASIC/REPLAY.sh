#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
"$ROOT/TOOLS/ensure-fuse.sh"
FUSE_BIN="$ROOT/fuse-root/usr/bin/fuse-sdl"
if [ ! -x "$FUSE_BIN" ]; then FUSE_BIN=$(command -v fuse-sdl); fi
export LD_LIBRARY_PATH="$ROOT/fuse-root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mkdir -p "$ROOT/REPLAYS/09-battleships"
# Run from archive root with prerequisites Xvfb, python-xlib and Pillow.
# Raw screenshots retain original runner names, mapped in KEYS-AND-TIMING.TXT.
exec python3 "$ROOT/TOOLS/run_fuse_demo_v18.py" \
  "$ROOT/09-battleships/BASIC/09-battleships.tzx" \
  --rom "$ROOT/TOOLS/ROM/48.rom" --fuse "$FUSE_BIN" \
  --out "$ROOT/REPLAYS/09-battleships" --display :25009 \
  --wait \
  1.4 \
  --after-key \
  r,Return \
  --after-wait \
  1.3 \
  --final-wait \
  2.0 \
  --fuse-speed \
  310 \
  --action-hold \
  0.05 \
  --pre-action-wait \
  7.0 \
  --sample-interval \
  0.0 \
  --samples \
  0 \
  --post-sample-hold \
  0.12 \
  --post-sample-wait \
  2.0 \
  --script-steps \
  'H:space:0.5|L:1|L:A1|L:B3|L:C5|L:D7|L:E9|L:F11|C:board-complete|H:8:0.6|H:9:0.6|C:after-fire' \
  --pre-action-capture \
  intro \
  --step-wait \
  2.0 \
  --finish-hold \
  0.05

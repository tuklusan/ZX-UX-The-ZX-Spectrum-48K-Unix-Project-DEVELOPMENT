#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
"$ROOT/TOOLS/ensure-fuse.sh"
FUSE_BIN="$ROOT/fuse-root/usr/bin/fuse-sdl"
if [ ! -x "$FUSE_BIN" ]; then FUSE_BIN=$(command -v fuse-sdl); fi
export LD_LIBRARY_PATH="$ROOT/fuse-root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mkdir -p "$ROOT/REPLAYS/15-endings"
# Run from archive root with prerequisites Xvfb, python-xlib and Pillow.
# Raw screenshots retain original runner names, mapped in KEYS-AND-TIMING.TXT.
exec python3 "$ROOT/TOOLS/run_fuse_demo_v18.py" \
  "$ROOT/15-endings/BASIC/15-endings.tzx" \
  --rom "$ROOT/TOOLS/ROM/48.rom" --fuse "$FUSE_BIN" \
  --out "$ROOT/REPLAYS/15-endings" --display :25015 \
  --wait \
  1.4 \
  --after-key \
  r,Return \
  --after-wait \
  1.1 \
  --final-wait \
  2.0 \
  --fuse-speed \
  280 \
  --action-hold \
  0.05 \
  --pre-action-wait \
  4.0 \
  --sample-interval \
  0.0 \
  --samples \
  0 \
  --post-sample-hold \
  0.12 \
  --post-sample-wait \
  2.0 \
  --script-steps \
  'K:space|S:n|W:2|C:computer-word|K:Return|C:human-turn' \
  --pre-action-capture \
  intro \
  --step-wait \
  1.8 \
  --finish-hold \
  0.05

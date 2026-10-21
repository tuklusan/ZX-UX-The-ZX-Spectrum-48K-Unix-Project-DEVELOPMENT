#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
"$ROOT/TOOLS/ensure-fuse.sh"
FUSE_BIN="$ROOT/fuse-root/usr/bin/fuse-sdl"
if [ ! -x "$FUSE_BIN" ]; then FUSE_BIN=$(command -v fuse-sdl); fi
export LD_LIBRARY_PATH="$ROOT/fuse-root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mkdir -p "$ROOT/REPLAYS/14-scuba"
# Run from archive root with prerequisites Xvfb, python-xlib and Pillow.
# Raw screenshots retain original runner names, mapped in KEYS-AND-TIMING.TXT.
exec python3 "$ROOT/TOOLS/run_fuse_demo_v18.py" \
  "$ROOT/14-scuba/BASIC/14-scuba.tzx" \
  --rom "$ROOT/TOOLS/ROM/48.rom" --fuse "$FUSE_BIN" \
  --out "$ROOT/REPLAYS/14-scuba" --display :25114 \
  --wait \
  1.5 \
  --after-key \
  r,Return \
  --after-wait \
  1.2 \
  --final-wait \
  2.5 \
  --fuse-speed \
  340 \
  --action-hold \
  0.35 \
  --pre-action-wait \
  27.0 \
  --sample-interval \
  0.0 \
  --samples \
  0 \
  --post-sample-hold \
  0.12 \
  --post-sample-wait \
  2.0 \
  --script-steps \
  'H:Return:0.8|H:f:0.7' \
  --pre-action-capture \
  intro-settled \
  --step-wait \
  2.4 \
  --finish-hold \
  0.05

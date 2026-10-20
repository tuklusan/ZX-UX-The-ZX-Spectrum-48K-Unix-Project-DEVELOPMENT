#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
"$ROOT/TOOLS/ensure-fuse.sh"
FUSE_BIN="$ROOT/fuse-root/usr/bin/fuse-sdl"
if [ ! -x "$FUSE_BIN" ]; then FUSE_BIN=$(command -v fuse-sdl); fi
export LD_LIBRARY_PATH="$ROOT/fuse-root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mkdir -p "$ROOT/REPLAYS/13-radio-power"
# Run from archive root with prerequisites Xvfb, python-xlib and Pillow.
# Raw screenshots retain original runner names, mapped in KEYS-AND-TIMING.TXT.
exec python3 "$ROOT/TOOLS/run_fuse_demo_v18.py" \
  "$ROOT/13-radio-power/BASIC/13-radio-power.tzx" \
  --rom "$ROOT/TOOLS/ROM/48.rom" --fuse "$FUSE_BIN" \
  --out "$ROOT/REPLAYS/13-radio-power" --display :25013 \
  --wait \
  1.4 \
  --after-key \
  r,Return \
  --after-wait \
  1.3 \
  --final-wait \
  2.0 \
  --fuse-speed \
  300 \
  --action-hold \
  0.05 \
  --pre-action-wait \
  5.0 \
  --sample-interval \
  0.0 \
  --samples \
  0 \
  --post-sample-hold \
  0.12 \
  --post-sample-wait \
  2.0 \
  --script-steps \
  'H:Return:0.5|H:y:0.45|L:AL|L:RADIO|L:SOUTHAMPTON|C:station-view|H:space:0.5' \
  --pre-action-capture \
  intro \
  --step-wait \
  1.7 \
  --finish-hold \
  0.05

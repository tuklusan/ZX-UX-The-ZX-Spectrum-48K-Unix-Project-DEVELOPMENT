#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
"$ROOT/TOOLS/ensure-fuse.sh"
FUSE_BIN="$ROOT/fuse-root/usr/bin/fuse-sdl"
if [ ! -x "$FUSE_BIN" ]; then FUSE_BIN=$(command -v fuse-sdl); fi
export LD_LIBRARY_PATH="$ROOT/fuse-root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mkdir -p "$ROOT/REPLAYS/38-morse-tutor"
# Run from archive root with prerequisites Xvfb, python-xlib and Pillow.
# Raw screenshots retain original runner names, mapped in KEYS-AND-TIMING.TXT.
exec python3 "$ROOT/TOOLS/run_fuse_demo_v18.py" \
  "$ROOT/38-morse-tutor/BASIC/38-morse-tutor.tzx" \
  --rom "$ROOT/TOOLS/ROM/48.rom" --fuse "$FUSE_BIN" \
  --out "$ROOT/REPLAYS/38-morse-tutor" --display :25038 \
  --wait \
  1.4 \
  --after-key \
  r,Return \
  --after-wait \
  1.2 \
  --final-wait \
  2.0 \
  --fuse-speed \
  120 \
  --action-hold \
  0.15 \
  --pre-action-wait \
  9.0 \
  --sample-interval \
  0.0 \
  --samples \
  0 \
  --post-sample-hold \
  0.12 \
  --post-sample-wait \
  2.0 \
  --script-steps \
  'K:6|W:0.7|C:morse-chart|K:space|C:back-menu' \
  --pre-action-capture \
  options-menu \
  --step-wait \
  0.15 \
  --finish-hold \
  0.05

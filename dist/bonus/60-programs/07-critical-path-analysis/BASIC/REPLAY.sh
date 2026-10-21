#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
"$ROOT/TOOLS/ensure-fuse.sh"
FUSE_BIN="$ROOT/fuse-root/usr/bin/fuse-sdl"
if [ ! -x "$FUSE_BIN" ]; then FUSE_BIN=$(command -v fuse-sdl); fi
export LD_LIBRARY_PATH="$ROOT/fuse-root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mkdir -p "$ROOT/REPLAYS/07-critical-path-analysis"
# Run from archive root with prerequisites Xvfb, python-xlib and Pillow.
# Raw screenshots retain original runner names, mapped in KEYS-AND-TIMING.TXT.
exec python3 "$ROOT/TOOLS/run_fuse_demo_v18.py" \
  "$ROOT/07-critical-path-analysis/BASIC/07-critical-path-analysis.tzx" \
  --rom "$ROOT/TOOLS/ROM/48.rom" --fuse "$FUSE_BIN" \
  --out "$ROOT/REPLAYS/07-critical-path-analysis" --display :25007 \
  --wait \
  1.5 \
  --after-key \
  r,Return \
  --after-wait \
  1.2 \
  --final-wait \
  2.5 \
  --fuse-speed \
  320 \
  --action-hold \
  0.35 \
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
  'L:1|L:2|L:3' \
  --pre-action-capture \
  intro-settled \
  --step-wait \
  2.4 \
  --finish-hold \
  0.05

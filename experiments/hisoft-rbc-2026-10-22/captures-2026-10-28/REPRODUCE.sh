#!/bin/sh
# Native RBC: rebuild genuine 48K framebuffer and live terminal captures.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
cd "$ROOT"
OUT=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28
STAGE=experiments/hisoft-rbc-2026-10-22/stage
SYSTEM=build/out/ZX-UX.tzx
CLI=$STAGE/native_rbc_cli.py
COMPILER=build/tmp/rbc-recovered/rbc
FRONTEND=${RBC_FRONTEND_DIR:?Set RBC_FRONTEND_DIR to the checked HiSoft source directory}
TAPE=${RBC_HISOFT_TAPE:?Set RBC_HISOFT_TAPE to the checked compiler TAP file}
ROM=src/zx-ux-sdk/rom/48.rom
BASIC=src/bonus/60-programs/42-bricklayer/BASIC/42-bricklayer.bas
SSX=src/bonus/60-programs/42-bricklayer/bin/42-bricklayer.ssx
mkdir -p build/tmp/rbc-round2
python -B "$CLI" "$BASIC" --compiler "$COMPILER" --frontend "$FRONTEND" \
  --tape "$TAPE" --rom "$ROM" --max 14000 -o build/tmp/rbc-round2/capture-compiled.ssx
cmp build/tmp/rbc-round2/capture-compiled.ssx "$SSX"
python -B src/zx-ux-sdk/rvm.py --headless --system "$SYSTEM" --frames 160 \
  --png "$OUT/bricklayer-start.png" "$SSX"
python -B src/zx-ux-sdk/rvm.py --headless --system "$SYSTEM" --frames 180 \
  --png "$OUT/roots-start.png" src/bonus/60-programs/56-roots/bin/56-roots.ssx
python -B src/zx-ux-sdk/rvm.py --headless --system "$SYSTEM" --frames 180 \
  --png "$OUT/snap-start.png" src/bonus/60-programs/16-snap/bin/16-snap.ssx
# BREAK is a deliberate kill; the emulator may return exit code 255.
python -B src/zx-ux-sdk/rvm.py --headless --system "$SYSTEM" \
  --keys 'a{WAIT 120}{BREAK}' --final --frames 400 \
  --png "$OUT/bricklayer-after-break.png" "$SSX" || test "$?" -eq 255
if command -v xvfb-run >/dev/null && command -v xterm >/dev/null && command -v scrot >/dev/null; then
  export ROOT OUT CLI COMPILER FRONTEND TAPE ROM BASIC
  xvfb-run -a --server-args='-screen 0 1280x800x24' sh -c '
    xterm -geometry 112x30+40+35 -fa "DejaVu Sans Mono" -fs 12 \
      -bg "#101820" -fg "#e9f1e9" -title "ZX-UX RBC native BASIC compiler - live run" \
      -e sh -c "cd \"\$ROOT\"; printf '\''ZX-UX RBC / strict native 48K BASIC / ras + rld\\n'\''; \
        python -B \"\$CLI\" \"\$BASIC\" --compiler \"\$COMPILER\" \
        --frontend \"\$FRONTEND\" --tape \"\$TAPE\" --rom \"\$ROM\" \
        --max 14000 -o build/tmp/rbc-round2/capture-terminal.ssx; sleep 12" &
    pid=$!; sleep 9; scrot -o "$OUT/native-cli-live-terminal.png"; wait "$pid"
  '
fi

# Real game controls: compare native Bricklayer's Z/M results with X/no-action.
python -B src/zx-ux-sdk/rvm.py --headless --system "$SYSTEM" --frames 750 \
  --keys 'a{WAIT 120}z{WAIT 200}z' \
  --png "$OUT/bricklayer-gameplay-z.png" "$SSX"
python -B src/zx-ux-sdk/rvm.py --headless --system "$SYSTEM" --frames 750 \
  --keys 'a{WAIT 120}z{WAIT 200}m' \
  --png "$OUT/bricklayer-gameplay-m.png" "$SSX"
python -B -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_bricklayer_gameplay.py -v
python -B -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_stop_shell.py -v
python -B -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_zx_tzx2bas.py -v

#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
"$ROOT/TOOLS/ensure-fuse.sh"
JOBS=${1:-8}
find "$ROOT" -mindepth 2 -maxdepth 2 -name REPLAY.sh -type f -print0 | sort -z | xargs -0 -P "$JOBS" -n 1 sh

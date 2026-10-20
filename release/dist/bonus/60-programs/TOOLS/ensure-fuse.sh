#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ -x "$ROOT/fuse-root/usr/bin/fuse-sdl" ]; then exit 0; fi
if command -v fuse-sdl >/dev/null 2>&1; then exit 0; fi
command -v dpkg-deb >/dev/null 2>&1 || { echo "Missing dpkg-deb; install FUSE SDL or use Debian/Ubuntu." >&2; exit 1; }
mkdir -p "$ROOT/fuse-root"
for deb in "$ROOT"/TOOLS/FUSE-debs/*.deb; do dpkg-deb -x "$deb" "$ROOT/fuse-root"; done
[ -x "$ROOT/fuse-root/usr/bin/fuse-sdl" ] || { echo 'No FUSE binary after unpack' >&2; exit 1; }

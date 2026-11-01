#!/usr/bin/env bash
# Collect all resolved Debian 13/amd64 APT dependencies and the Pillow wheel.
set -euo pipefail
cd "$(dirname "$0")/../.."
. /etc/os-release
if [[ "$ID" != debian || "${VERSION_ID%%.*}" != 13 || "$(dpkg --print-architecture)" != amd64 ]]; then
  echo 'Requires Debian 13/amd64' >&2; exit 1
fi
if (( EUID == 0 )); then apt=(apt-get); else apt=(sudo apt-get); fi
base="$PWD/build/dependencies/debian-13-amd64"
mkdir -p "$base/apt/partial" "$base/pip"
"${apt[@]}" update
"${apt[@]}" install -y --no-install-recommends python3-venv ca-certificates
# Use empty installed-package status: also fetch dependencies already in the base.
empty_status=$(mktemp)
trap 'rm -f "$empty_status"' EXIT
"${apt[@]}" -y --download-only --no-install-recommends \
  -o "Dir::State::status=$empty_status" \
  -o "Dir::Cache::archives=$base/apt/" \
  install bash ca-certificates coreutils git git-lfs build-essential curl \
          python3 python3-venv xvfb x11-utils libxtst6 libx11-6 fuse-emulator-sdl
venv=$(mktemp -d)
trap 'rm -f "$empty_status"; rm -rf "$venv"' EXIT
python3 -m venv "$venv"
"$venv/bin/python" -m pip download --only-binary=:all: \
  --dest "$base/pip" 'Pillow>=12.1,<13'
shopt -s nullglob
debs=("$base"/apt/*.deb)
wheels=("$base"/pip/Pillow-*.whl "$base"/pip/pillow-*.whl)
((${#debs[@]} > 0 && ${#wheels[@]} > 0)) || {
  echo 'Incomplete Debian or Pillow download' >&2; exit 1
}
printf 'Collected %d Debian packages and %d Pillow wheels\n' \
  "${#debs[@]}" "${#wheels[@]}"

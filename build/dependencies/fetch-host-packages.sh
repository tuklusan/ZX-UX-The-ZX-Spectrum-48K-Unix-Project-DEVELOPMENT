#!/usr/bin/env bash
# Run on an online Debian/Ubuntu host to collect its own APT and Pillow installers.
# The checked-in .deb files are Debian 13/amd64; do not install them on Ubuntu.
# For a useful offline bundle, collect on a fresh matching distro/architecture.
set -euo pipefail
cd "$(dirname "$0")/../.."
. /etc/os-release
case "$ID" in
  debian|ubuntu) ;;
  *) echo "Requires Debian or Ubuntu: $ID" >&2; exit 1 ;;
esac
arch=$(dpkg --print-architecture)
dst="$PWD/build/dependencies/$ID-$VERSION_ID-$arch"
mkdir -p "$dst/apt" "$dst/pip/"

sudo apt-get update
# Install the wheel-download bootstrap on this *collector*, not the offline host.
sudo apt-get install -y python3 python3-venv
# Download the named packages and dependencies not already on this machine.
sudo apt-get -y --download-only \
  -o Dir::Cache::archives="$dst/apt/" \
  install software-properties-common build-essential curl python3 python3-venv \
  xvfb x11-utils libxtst6 libx11-6 fuse-emulator-sdl
venv=$(mktemp -d)
trap 'rm -rf "$venv"' EXIT
python3 -m venv "$venv/venv"
"$venv/venv/bin/python" -m pip download --only-binary=:all: \
  --dest "$dst/pip/" 'Pillow>=12.1,<13'
printf 'Saved host-matching APT/Pillow downloads to %s\n' "$dst"

#!/usr/bin/env bash
# Install the tracked Debian 13/amd64 package closure without network access.
set -euo pipefail
cd "$(dirname "$0")/../.."
. /etc/os-release
if [[ "$ID" != debian || "${VERSION_ID%%.*}" != 13 || "$(dpkg --print-architecture)" != amd64 ]]; then
  echo 'Requires Debian 13/amd64' >&2; exit 1
fi
base="$PWD/build/dependencies/debian-13-amd64"
shopt -s nullglob
debs=("$base"/apt/*.deb)
wheels=("$base"/pip/Pillow-*.whl "$base"/pip/pillow-*.whl)
((${#debs[@]} > 0 && ${#wheels[@]} > 0)) || {
  echo 'APT closure or Pillow wheel missing; run fetch-host-packages.sh first' >&2
  exit 1
}
sudo apt-get -y --no-download --allow-downgrades \
  -o Dir::Etc::sourcelist=/dev/null -o Dir::Etc::sourceparts=- \
  install "${debs[@]}"
python3 -m venv /tmp/zxux-py
/tmp/zxux-py/bin/python -m pip install --no-index --find-links "$base/pip" 'Pillow>=12.1,<13'
sudo install -m 755 build/dependencies/sjasmplus/sjasmplus-1.24.0-linux-amd64 \
  /usr/local/bin/sjasmplus
sjasmplus --version
/tmp/zxux-py/bin/python -c 'from PIL import Image, ImageGrab; print("Pillow", Image.__version__)'

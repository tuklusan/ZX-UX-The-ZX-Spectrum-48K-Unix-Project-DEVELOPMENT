#!/usr/bin/env bash
# Disposable GitHub runner: rebuild dist/ from scratch and compare against HEAD.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONDONTWRITEBYTECODE=1

set -euxo pipefail
# On a prepared Debian 13 machine, reuse the tracked offline installers.
# A disposable GitHub Ubuntu runner still bootstraps its dependencies.
if test -x /usr/local/bin/sjasmplus \
  && test -x /usr/bin/fuse-sdl \
  && command -v Xvfb >/dev/null \
  && test -f /usr/share/fuse/fuse.font \
  && test -x /tmp/zxux-py/bin/python \
  && /tmp/zxux-py/bin/python -c 'from PIL import Image, ImageGrab, ImageChops; assert hasattr(Image.new("L",(1,1)), "get_flattened_data")'; then
  echo 'Using locally installed build dependencies'
else
  sudo apt-get update
  sudo apt-get install -y software-properties-common
  . /etc/os-release
  if [ "$ID" = ubuntu ]; then
    sudo add-apt-repository -y universe
    sudo apt-get update
  fi
  sudo apt-get install -y build-essential curl python3 python3-venv xvfb x11-utils libxtst6 libx11-6 fuse-emulator-sdl
  python3 -m venv /tmp/zxux-py
  /tmp/zxux-py/bin/python -m pip install 'Pillow>=12.1,<13'
  curl -fL --retry 3 https://github.com/z00m128/sjasmplus/releases/download/v1.24.0/sjasmplus-1.24.0-src.tar.xz -o /tmp/sjasmplus-src.tar.xz
  tar -xJf /tmp/sjasmplus-src.tar.xz -C /tmp
  make -C /tmp/sjasmplus-1.24.0 -j2
  sudo install -m 755 /tmp/sjasmplus-1.24.0/sjasmplus /usr/local/bin/sjasmplus
fi
export PATH="/tmp/zxux-py/bin:$PATH"
sjasmplus --version
command -v fuse-sdl
test -f /usr/share/fuse/fuse.font
/tmp/zxux-py/bin/python -c 'from PIL import Image, ImageGrab, ImageChops; assert hasattr(Image.new("L",(1,1)), "get_flattened_data"); print("Pillow ready")'

# Run the same targeted checks locally and through Actions.
if [[ "${1:-}" == "--targeted" ]]; then
  mkdir -p cleanroom-logs/targeted
  export ZXUX_FUSE_LOG_DIR="$PWD/cleanroom-logs/targeted/fuse-processes"
  mkdir -p "$ZXUX_FUSE_LOG_DIR"
  if ! python3 -B build/build.py /usr/local/bin/sjasmplus >cleanroom-logs/targeted/build.log 2>&1; then
    tail -n 40 cleanroom-logs/targeted/build.log
    exit 1
  fi
  games=(39-compspacegames-SpaceGames-11 50-monsters--Monsters)
  for game in "${games[@]}"; do
    rm -f "dist/screenshots/rbc/rvm/www.thespectrumshow.net/$game.png" \
          "dist/screenshots/rbc/fuse/www.thespectrumshow.net/$game.png"
  done
  rm -f dist/screenshots/rfc/rvm/demo.png
  failures=0
  capture() {
    local name="$1" rc=0
    shift
    timeout --signal=TERM --kill-after=30s 60m "$@" \
      >"cleanroom-logs/targeted/$name.log" 2>&1 || rc=$?
    printf '%s %s (exit %s)\n' "$([[ "$rc" == 0 ]] && echo PASS || echo FAIL)" "$name" "$rc"
    tail -n 15 "cleanroom-logs/targeted/$name.log"
    if [[ "$rc" != 0 && "$name" == fuse-* ]]; then
      # Expose real failed-capture PNGs for visual review in the job log.
      # They remain unchanged; base64 is only a lossless transport.
      for png in "$ZXUX_FUSE_LOG_DIR"/*.before-input.png \
                 "$ZXUX_FUSE_LOG_DIR"/*.after-input.png \
                 "$ZXUX_FUSE_LOG_DIR"/*.first-input.png; do
        [[ -f "$png" ]] || continue
        printf 'ZXUX_CAPTURE_PNG:%s:' "$(basename "$png")"
        base64 -w0 -- "$png"
        printf '\n'
      done
    fi
    if [[ "$rc" != 0 ]]; then failures=$((failures + 1)); fi
  }
  # Fuse's Phantom Typist is a ROM tape loader, not a gameplay typist.
  # Test its Keystroke mode without changing normal Fuse captures.
  fuse_phantom="$(mktemp /tmp/zxux-fuse-phantom.XXXXXX)"
  trap 'rm -f "$fuse_phantom"' EXIT
  cat >"$fuse_phantom" <<'FUSE_PHANTOM'
#!/usr/bin/env bash
exec /usr/bin/fuse-sdl --phantom-typist-mode Keystroke "$@"
FUSE_PHANTOM
  chmod 700 "$fuse_phantom"
  for game in "${games[@]}"; do
    capture "rvm-$game" python3 -B build/tools/basic_portfolio.py \
      --only "$game" --jobs 1
    capture "fuse-$game" python3 -B build/tools/basic_fuse_portfolio.py \
      --fuse "$fuse_phantom" --assets /usr/share/fuse --only "$game" --jobs 1
  done
  capture rvm-forth-demo python3 -B -c 'import sys; sys.path.insert(0, "build/tools"); from compiler_portfolio import cases, capture_rvm; demo = [c for c in cases({"rfc"}) if c[1] == "demo"]; assert len(demo) == 1, "Forth demo unavailable"; capture_rvm(*demo[0], 1500)'
  python3 -B - <<'PY' || failures=$((failures + 1))
from pathlib import Path
from PIL import Image
import shutil

out = Path('cleanroom-logs/targeted')
images = []
for game in ('39-compspacegames-SpaceGames-11', '50-monsters--Monsters'):
    for engine in ('rvm', 'fuse'):
        images.append((Path('dist/screenshots/rbc') / engine
                       / 'www.thespectrumshow.net' / (game + '.png'),
                       engine + '-' + game + '.png',
                       (576, 448) if engine == 'rvm' else (320, 240)))
images.append((Path('dist/screenshots/rfc/rvm/demo.png'),
               'forth-rvm-demo.png', (576, 448)))
errors = 0
for source, name, dimensions in images:
    if not source.is_file():
        print('MISSING', source)
        errors += 1
        continue
    try:
        with Image.open(source) as picture:
            picture.verify()
        with Image.open(source) as picture:
            if picture.size != dimensions or picture.getbbox() is None:
                raise ValueError('blank or incorrectly sized screenshot')
        shutil.copy2(source, out / name)
        print('VERIFIED', source)
    except (OSError, ValueError, RuntimeError) as error:
        print('INVALID', source, error)
        errors += 1
if errors:
    raise SystemExit(errors)
PY
  if [[ "$failures" != 0 ]]; then
    printf 'Targeted verification: %s failures\n' "$failures" >&2
    exit 1
  fi
  echo 'Targeted verification: 5 captures and screenshots passed'
  exit 0
fi
if [[ "$#" != 0 ]]; then
  echo 'Use --targeted or no arguments' >&2
  exit 2
fi

set -uo pipefail
mkdir -p cleanroom-logs
git ls-tree -r HEAD dist > cleanroom-logs/baseline.tree
find dist -type f | sort > cleanroom-logs/baseline-paths.txt
rm -rf dist
test ! -e dist || exit 2
printf 'head=%s\n' "$(git rev-parse HEAD)" > cleanroom-logs/meta.txt
for entry in build c48-rvm rbc-rvm compilers-rvm c48-fuse rbc-fuse compilers-fuse gallery; do
  if [[ "$entry" == *-fuse ]]; then
    export ZXUX_FUSE_LOG_DIR="$PWD/cleanroom-logs/fuse-processes/$entry"
    mkdir -p "$ZXUX_FUSE_LOG_DIR"
  else
    unset ZXUX_FUSE_LOG_DIR || true
  fi
  case "$entry" in
    build) cmd=(python3 -B build/build.py /usr/local/bin/sjasmplus) ;;
    c48-rvm) cmd=(python3 -B build/tools/portfolio.py --jobs 8) ;;
    rbc-rvm) cmd=(python3 -B build/tools/basic_portfolio.py --jobs 8) ;;
    compilers-rvm) cmd=(python3 -B build/tools/compiler_portfolio.py --engine rvm --jobs 8) ;;
    c48-fuse) cmd=(python3 -B build/tools/fuse_portfolio.py --fuse /usr/bin/fuse-sdl --assets /usr/share/fuse --jobs 8) ;;
    rbc-fuse) cmd=(python3 -B build/tools/basic_fuse_portfolio.py --fuse /usr/bin/fuse-sdl --assets /usr/share/fuse --jobs 8) ;;
    compilers-fuse) cmd=(python3 -B build/tools/compiler_portfolio.py --engine fuse --fuse /usr/bin/fuse-sdl --assets /usr/share/fuse --jobs 8) ;;
    gallery) cmd=(python3 -B build/tools/gallery_index.py) ;;
  esac
  printf '%s: %q ' "$entry" "${cmd[@]}" >> cleanroom-logs/commands.txt
  printf '\n' >> cleanroom-logs/commands.txt
  printf 'START %s %s\n' "$entry" "$(date -u +%FT%TZ)"
  if timeout --signal=TERM --kill-after=30s 175m "${cmd[@]}" > "cleanroom-logs/$entry.log" 2>&1; then
    rc=0
  else
    rc=$?
  fi
  printf '%s\t%d\n' "$entry" "$rc" >> cleanroom-logs/exit-codes.tsv
  printf 'END %s rc=%s %s\n' "$entry" "$rc" "$(date -u +%FT%TZ)"
  tail -n 12 "cleanroom-logs/$entry.log"
  if [ "$entry" = build ] && [ "$rc" -ne 0 ]; then
    echo 'Build failed: later stages need compiled files; see audit.'
    break
  fi
done

mkdir -p cleanroom-logs
python3 - <<'PY'
from pathlib import Path
import collections, json, subprocess
root = Path('cleanroom-logs')
baseline = {}
if (root/'baseline.tree').exists():
    for line in (root/'baseline.tree').read_text().splitlines():
        meta, _, name = line.partition('\t')
        if name:
            baseline[name] = meta.split()[2]
actual = {p.as_posix() for p in Path('dist').rglob('*') if p.is_file()} if Path('dist').exists() else set()
missing = sorted(set(baseline)-actual)
added = sorted(actual-set(baseline))
changed = []
for name in sorted(actual & set(baseline)):
    sha = subprocess.run(['git','hash-object','--',name], text=True, capture_output=True).stdout.strip()
    if sha != baseline[name]:
        changed.append(name)
codes = {}
if (root/'exit-codes.tsv').exists():
    for row in (root/'exit-codes.tsv').read_text().splitlines():
        name, rc = row.split('\t')
        codes[name] = int(rc)
count_by_prefix = lambda names: dict(sorted(collections.Counter('/'.join(s.split('/')[:4]) for s in names).items()))
report = {'head': subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
          'baseline_file_count':len(baseline),'rebuilt_file_count':len(actual),
          'missing_count':len(missing),'extra_count':len(added),'changed_count':len(changed),
          'missing':missing,'extra':added,'changed':changed,
          'missing_by_directory':count_by_prefix(missing),
          'stage_exit_codes':codes}
(root/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
(root/'audit-summary.txt').write_text(
    f"Baseline={len(baseline)} Rebuilt={len(actual)} Missing={len(missing)} Extra={len(added)} Changed={len(changed)}\n"
    + '\n'.join(f"{k}: {v}" for k,v in codes.items()) + '\n'
    + 'Missing files:\n' + '\n'.join(missing) + '\n')
print((root/'audit-summary.txt').read_text()[:12000])
PY

python3 - <<'PY'
import json, pathlib, sys
p = pathlib.Path('cleanroom-logs/audit.json')
if not p.exists():
    sys.exit('No audit generated')
r = json.loads(p.read_text())
required = {'build','c48-rvm','rbc-rvm','compilers-rvm','c48-fuse','rbc-fuse','compilers-fuse','gallery'}
failures = r['missing_count'] or (required - r['stage_exit_codes'].keys()) or any(rc for rc in r['stage_exit_codes'].values())
if failures:
    sys.exit('INCOMPLETE: see zx-ux-cleanroom-audit artifact')
print('PASS: all baseline distribution paths reconstructed')
PY

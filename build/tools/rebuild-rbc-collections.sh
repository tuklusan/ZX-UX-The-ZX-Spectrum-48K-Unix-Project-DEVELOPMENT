#!/usr/bin/env bash
# One project entry point for manual and GitHub-runner collections rebuilds.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONDONTWRITEBYTECODE=1
mode="${1:---build}"
case "$mode" in --build|--publish) ;; *) echo 'Use --build or --publish' >&2; exit 2 ;; esac

python3 -B build/tools/check_portability.py
python3 -B build/tools/smoke_test.py
python3 -B build/tools/compile-rbc-collections.py
bash build/tools/cleanroom-build-using-github-action-runner.sh
/tmp/zxux-py/bin/python -B -m unittest discover -s tests

if [[ "$mode" == --publish ]]; then
  git fetch origin main
  test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" || {
    echo 'Remote main moved; publication refused' >&2; exit 1;
  }
  git add -A -- dist \
    src/assets/basic-src/original-sinclair-basic-collections/Granada-Publishing \
    src/assets/basic-src/original-sinclair-basic-collections/numerical-analysis \
    src/assets/basic-src/original-sinclair-basic-collections/www.thespectrumshow.net \
    build/tools .github/workflows/rebuild-rbc-collections.yml \
    src/zx-ux-sdk/tools/basicpack.py tests/test_rbc_distribution.py tests/test_capture_replay.py
fi

python3 -B - "$mode" "${ZXUX_PRIVATE_CHECKER:-}" <<'PYVERIFY'
from pathlib import Path
import subprocess
import sys
import tempfile

mode, checker = sys.argv[1:]
staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z'])
paths = [Path(x.decode()) for x in staged.split(b'\0') if x] if mode == '--publish' else []
roots = ('dist/', 'build/tools/', '.github/workflows/rebuild-rbc-collections.yml',
         'src/zx-ux-sdk/tools/basicpack.py', 'tests/test_rbc_distribution.py',
         'tests/test_capture_replay.py')
collections = ('Granada-Publishing', 'numerical-analysis', 'www.thespectrumshow.net')
if mode == '--publish':
    if not paths:
        raise SystemExit('No changes to publish')
    for path in paths:
        name = path.as_posix()
        if name.startswith(roots):
            continue
        if not any(name.startswith('src/assets/basic-src/original-sinclair-basic-collections/' + c + '/')
                   and '/bin/' in name for c in collections):
            raise SystemExit('Unexpected staged file: ' + name)

if checker:
    authored = [Path(name) for name in (
        'build/tools/rebuild-rbc-collections.sh',
        'build/tools/compile-rbc-collections.py',
        'build/tools/capture_replay.py',
        'build/tools/rbc_replays.json',
        'build/tools/gallery_index.py',
        'src/zx-ux-sdk/tools/basicpack.py',
        'tests/test_rbc_distribution.py',
        'tests/test_capture_replay.py')]
    check_files = paths if mode == '--publish' else authored
    args = [sys.executable, '-B', checker, 'check']
    for path in check_files:
        if not path.is_file():
            continue  # Deleted files were checked by staged-path validation.
        parts = path.parts
        if (len(parts) >= 6 and parts[:3] == ('dist', 'assets', 'basic-src') or
                len(parts) >= 6 and parts[:3] == ('dist', 'assets', 'rbc-src')):
            original = Path('src/assets/basic-src/original-sinclair-basic-collections') / parts[3] / parts[4] / 'BASIC' / Path(*parts[5:])
            if not original.is_file() or path.read_bytes() != original.read_bytes():
                raise SystemExit('Original BASIC source changed: ' + str(path))
            continue  # Previously archived bytes; never rewrite for prose checks.
        if path.suffix.lower() in ('.png', '.ssx', '.tzx', '.sso', '.ssa', '.bin', '.rom'):
            continue
        args.extend(('--file', str(path)))
    with tempfile.TemporaryDirectory(prefix='zxux-prewrite-') as folder:
        message = Path(folder) / 'message.txt'
        message.write_text('Rebuild verified RBC collections and both screenshot portfolios\n')
        args.extend(('--message-file', str(message), '--command', 'git push origin HEAD:refs/heads/main'))
        subprocess.run(args, check=True)
elif mode == '--publish':
    raise SystemExit('Private checker required before publication')
PYVERIFY

if [[ "$mode" == --publish ]]; then
  git fetch origin main
  test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" || {
    echo 'Remote main moved; publication refused' >&2; exit 1;
  }
  git -c user.name='ZX-UX release runner' \
      -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
      commit -m 'Rebuild verified RBC collections and both screenshot portfolios'
  git push origin HEAD:refs/heads/main
  git fetch origin main
  test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
  test "$(git rev-parse HEAD^{tree})" = "$(git rev-parse origin/main^{tree})"
fi

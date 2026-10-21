#!/usr/bin/env python3
"""Check the relocatable source-only project layout without extra build tools."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'build/tools'


def main():
    required = (ROOT / 'build/build.py', ROOT / 'src/zx-ux',
                ROOT / 'src/zx-ux-sdk', ROOT / 'src/assets/c48-src',
                ROOT / 'src/bonus/60-programs',
                ROOT / 'src/docs')
    for item in required:
        if not item.exists():
            raise RuntimeError('Missing portable component: ' + str(item))
    for name in ('release.py', 'portfolio.py', 'fuse_portfolio.py',
                 'gallery.py', 'fuse_boot.py', 'smoke_test.py'):
        path = TOOLS / name
        if not path.is_file():
            raise RuntimeError('Missing local build tool: ' + name)
        compile(path.read_bytes(), str(path), 'exec')
    compile((ROOT / 'build/build.py').read_bytes(), str(ROOT / 'build/build.py'), 'exec')
    if not isinstance(json.loads((TOOLS / 'runs.json').read_text()), dict):
        raise RuntimeError('Invalid local run configurations')
    folders = sorted(p for p in (ROOT / 'src/bonus/60-programs').iterdir()
                     if p.is_dir() and p.name[:2].isdigit())
    if len(folders) != 60:
        raise RuntimeError('Expected exactly 60 original BASIC program directories')
    for folder in folders:
        listings = list((folder / 'BASIC').glob('*.bas'))
        if len(listings) != 1 or (folder / 'C48').exists():
            raise RuntimeError('Unexpected BASIC program directory: ' + folder.name)
    # Run the launcher from outside the project; the current directory must not matter.
    with tempfile.TemporaryDirectory() as elsewhere:
        result = subprocess.run([sys.executable, '-B', str(TOOLS / 'release.py'),
                                 '--help'], cwd=elsewhere, capture_output=True, text=True)
    if result.returncode or '--build-only' not in result.stdout:
        raise RuntimeError('Relocatable launcher failed from a foreign working directory')
    print('PASS: self-contained source layout, 60 BASIC programs, relocatable launcher')


if __name__ == '__main__':
    main()

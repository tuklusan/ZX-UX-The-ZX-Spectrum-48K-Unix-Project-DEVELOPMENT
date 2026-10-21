#!/usr/bin/env python3
"""Check the standalone release layout without invoking an assembler or emulator."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'build/tools'
EXPECTED_TOOLS = ('release.py', 'portfolio.py', 'fuse_portfolio.py',
                  'gallery.py', 'fuse_boot.py')


def main():
    for path in (ROOT / 'build/build.py', ROOT / 'src/zx-ux',
                 ROOT / 'src/zx-ux-sdk', ROOT / 'src/bonus/60-programs',
                 ROOT / 'dist/assets/c48-src', ROOT / 'dist/sdk/bin/py'):
        if not path.exists():
            raise RuntimeError('Missing portable component: ' + str(path))
    for name in EXPECTED_TOOLS:
        path = TOOLS / name
        if not path.is_file():
            raise RuntimeError('Missing local tool: ' + name)
        compile(path.read_bytes(), str(path), 'exec')
    cases = TOOLS / 'runs.json'
    if not isinstance(json.loads(cases.read_text(encoding='utf-8')), dict):
        raise RuntimeError('Invalid local scenario data')
    programs = ROOT / 'src/bonus/60-programs'
    folders = [p for p in programs.iterdir() if p.is_dir() and p.name[:2].isdigit()]
    if len(folders) != 60:
        raise RuntimeError('Expected 60 original BASIC program folders')
    for folder in folders:
        listings = list((folder / 'BASIC').glob('*.bas'))
        if len(listings) != 1 or (folder / 'C48').exists():
            raise RuntimeError('Unexpected original BASIC folder: ' + folder.name)
    # Launch from a different working directory to catch cwd-based launch paths.
    with tempfile.TemporaryDirectory() as elsewhere:
        result = subprocess.run([sys.executable, '-B', str(TOOLS / 'release.py'),
                                 '--help'], cwd=elsewhere, capture_output=True, text=True)
    if result.returncode or '--build-only' not in result.stdout:
        raise RuntimeError('Portable launcher cannot run from elsewhere')
    print('PASS portable layout: 60 BASIC programs, local tools and foreign cwd')


if __name__ == '__main__':
    main()

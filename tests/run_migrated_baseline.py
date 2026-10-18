#!/usr/bin/env python3
"""External regression adapter for the relocated beta-0.0.6-equivalent build.

Reconstitutes only the legacy test harness's expected paths under retained
tests/.work/migrated, outside the release directory.
It runs on byte-exact files produced by release/build/build.py.
"""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'release'
TMP = RELEASE / 'build'
WS = ROOT / 'tests/.work/migrated'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tap2sna', required=True)
    ap.add_argument('--skoolkit', required=True, help='Parent of the checked skoolkit package')
    ap.add_argument('--only', default='', help='Comma-delimited suite test names; empty means all')
    args = ap.parse_args()
    if WS.exists():
        if WS.is_symlink():
            raise RuntimeError('Unsafe test workspace symlink')
        shutil.rmtree(WS)
    WS.mkdir(parents=True)
    for source, dest in ((TMP / 'src', WS / 'src'),
                         (TMP / 'sdk', WS / 'sdk'),
                         (TMP / 'out', WS / 'build'),
                         (RELEASE / 'dist/assets/c48-src', WS / 'programs/c48'),
                         (ROOT / 'tests', WS / 'tests'),
                         (ROOT / 'tools', WS / 'tools'),
                         (ROOT / 'docs', WS / 'docs')):
        shutil.copytree(source, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.work'))
    shutil.copytree(ROOT / 'tests/sdk', WS / 'sdk/tests')
    # Tests alone keep the scripted input cases; build sources need none.
    assert (WS / 'sdk/tests/runs.json').is_file()
    (WS / 'rom').mkdir()
    shutil.copyfile(RELEASE / 'src/zx-ux/rom/48.rom', WS / 'rom/48.rom')
    c48 = WS / 'build/c48'
    c48.mkdir(exist_ok=True)
    for source in (RELEASE / 'dist/assets/c48-bin/ssx').glob('*.ssx'):
        shutil.copyfile(source, c48 / source.name)
    # Historical suite consumes a legacy-location boot tape and SDK files.
    for old, name in (('legacy-c48-demos.tzx', 'c48-demos.tzx'),
                      ('legacy-c48-multitask.tzx', 'c48-multitask.tzx')):
        shutil.copyfile(ROOT / 'tests/fixtures' / old, WS / 'build' / name)
    for name in ('ZX-UX.tzx',):
        shutil.copyfile(RELEASE / 'dist/zx-ux' / name, WS / 'build' / name)
    env = dict(os.environ, PYTHONPATH=args.skoolkit + os.pathsep + str(WS / 'sdk'))
    cmd = [sys.executable, args.tap2sna, '-c', 'fast-load=1', '-d', str(WS / 'build'),
           str(WS / 'build/ZX-UX.tzx'), 'test.z80']
    print('Generating fresh baseline snapshot', flush=True)
    subprocess.run(cmd, cwd=WS, env=env, check=True)
    print('Checking beta-0.0.7 merged boot layout from fresh symbols and tape', flush=True)
    subprocess.run([sys.executable, str(ROOT / 'tests/test_boot_beta7.py')], cwd=ROOT, env=env, check=True)
    # Some independent batches read this fixture before another test compiles it.
    (WS / 'build/ssx').mkdir(exist_ok=True)
    subprocess.run([sys.executable, 'sdk/bin/rcc', 'tests/c/ssxargs.c',
                    '-o', 'build/ssx/ssxargs.ssx'], cwd=WS, env=env, check=True)
    cmd = [sys.executable, '-u', 'tests/suite.py']
    if args.only:
        cmd += ['-k', args.only]
    print('Running migrated regression suite', flush=True)
    return subprocess.run(cmd, cwd=WS, env=env).returncode


if __name__ == '__main__':
    sys.exit(main())

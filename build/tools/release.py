#!/usr/bin/env python3
"""Build ZX-UX from a portable developer folder and optionally capture galleries.

Examples (run from the unpacked folder, regardless of its name):
  python3 build/tools/release.py --build-only
  python3 build/tools/release.py --fuse /usr/bin/fuse-sdl --fuse-assets /usr/share/fuse

The complete repository-only regression suite is not bundled here.
The source builder and gallery tools have no dependency on files outside
this folder; SJASMPlus, Fuse, Xvfb, and Pillow are external programs/packages.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent


def run(*args):
    print('+', ' '.join(str(s) for s in args), flush=True)
    subprocess.run([str(x) for x in args], cwd=ROOT, check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sjasm', default=shutil.which('sjasmplus'))
    p.add_argument('--fuse', default=shutil.which('fuse-sdl'))
    p.add_argument('--fuse-assets', default='/usr/share/fuse')
    p.add_argument('--fuse-libdir', default='')
    p.add_argument('--build-only', action='store_true',
                   help='build the distribution without running emulators')
    p.add_argument('--skip-fuse', action='store_true',
                   help='build and capture RVM screenshots without Fuse')
    args = p.parse_args()
    if not args.sjasm:
        p.error('SJASMPlus executable required (PATH or --sjasm)')
    sjasm = shutil.which(args.sjasm)
    if not sjasm or not Path(sjasm).is_file():
        p.error('SJASMPlus executable not found: ' + args.sjasm)
    if not args.build_only and not args.skip_fuse:
        if not args.fuse or not shutil.which(args.fuse):
            p.error('Fuse SDL required (PATH or --fuse)')
        if not (Path(args.fuse_assets) / 'fuse.font').is_file():
            p.error('Fuse support files required (use --fuse-assets)')
    py = sys.executable
    run(py, '-B', ROOT / 'build/build.py', Path(sjasm).resolve())
    if args.build_only:
        print('ZX-UX distribution rebuilt.')
        return 0
    run(py, '-B', TOOLS / 'portfolio.py')
    run(py, '-B', TOOLS / 'basic_portfolio.py')
    if args.skip_fuse:
        print('ZX-UX rebuilt and RVM gallery generated.')
        return 0
    command = [py, '-B', TOOLS / 'fuse_portfolio.py', '--fuse', args.fuse,
               '--assets', args.fuse_assets]
    if args.fuse_libdir:
        command += ['--libdir', args.fuse_libdir]
    run(*command)
    command[2] = str(TOOLS / 'basic_fuse_portfolio.py')
    run(*command)
    print('ZX-UX rebuilt; C48 and BASIC RVM/Fuse galleries generated.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

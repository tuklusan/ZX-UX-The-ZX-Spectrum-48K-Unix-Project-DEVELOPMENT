#!/usr/bin/env python3
"""Build and verify ZX-UX, then capture the entire C48 portfolio in RVM and Fuse.

    python3 tools/release.py

Requires Python 3, SJASMPlus, Fuse SDL, Xvfb and Pillow. Optional --fuse,
--fuse-assets and --fuse-libdir locate an externally installed Fuse. The
builder uses the checked-in ZX-UX ROM. No history, checksum manifests,
independent release wrappers or program recompilation for screenshots.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    print('+', ' '.join(str(s) for s in args), flush=True)
    subprocess.run([str(x) for x in args], cwd=ROOT, check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sjasm', default=shutil.which('sjasmplus'))
    p.add_argument('--fuse', default=shutil.which('fuse-sdl'))
    p.add_argument('--fuse-assets', default='/usr/share/fuse')
    p.add_argument('--fuse-libdir', default='')
    args = p.parse_args()
    if not args.sjasm or not Path(args.sjasm).is_file():
        p.error('SJASMPlus executable required (PATH or --sjasm)')
    if not args.fuse or not Path(args.fuse).is_file():
        p.error('Fuse SDL required (PATH or --fuse)')
    if not (Path(args.fuse_assets) / 'fuse.font').is_file():
        p.error('Fuse support files required (use --fuse-assets)')
    py = sys.executable
    run(py, '-B', 'release/build/build.py', args.sjasm)
    for pattern in ('test_c48_constant_ranges.py', 'test_tzx_kernel_apps.py',
                    'test_turbo_segments_beta7.py'):
        run(py, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', pattern)
    run(py, '-B', 'tests/test_boot_beta7.py')
    run(py, '-B', 'tests/test_beta010_release.py')
    run(py, '-B', 'tools/portfolio.py')
    cmd = [py, '-B', 'tools/fuse_portfolio.py', '--fuse', args.fuse,
           '--assets', args.fuse_assets]
    if args.fuse_libdir:
        cmd += ['--libdir', args.fuse_libdir]
    run(*cmd)
    print('ZX-UX build verified; RVM and Fuse galleries generated.')


if __name__ == '__main__':
    main()

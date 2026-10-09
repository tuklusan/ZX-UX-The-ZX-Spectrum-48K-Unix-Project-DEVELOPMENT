#!/usr/bin/env python3
"""Write the release assets into release/ from what build/ holds.

  python3 tools/mkrelease.py [LOGDIR]

Run after: tools/build.py, tools/t.sh (build/test.z80), tools/mktapes.py,
tools/mtsnap.py, tests/ssxrun.py --png build/shots, sdk/tests/oracle.py
--png build/shots-vm, tools/gallery.py.  LOGDIR holds the test logs
(suite.txt, oracle.txt, oracle-bytecode.txt, ssxrun.txt, ras.txt) and any
extra screenshots (*.png) for test-results.zip.
"""
import glob
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'build')
R = os.path.join(ROOT, 'release')
FIXED = (2026, 1, 1, 0, 0, 0)


def write(zname, items):
    """items: (path on disk, name in the archive)"""
    p = os.path.join(R, zname)
    with zipfile.ZipFile(p, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for src, name in items:
            info = zipfile.ZipInfo(name, FIXED)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o755 << 16 if os.access(src, os.X_OK) and src.endswith('sjasmplus') else 0o644 << 16
            z.writestr(info, open(src, 'rb').read())
    print('%-32s %8d bytes, %d files' % (zname, os.path.getsize(p), len(items)))


def main(argv):
    logs = argv[0] if argv else None
    os.makedirs(R, exist_ok=True)
    b = lambda n: (os.path.join(B, n), n)
    write('runixz80-tzx.zip', [b('runixz80.tzx')])
    write('runixz80-tap.zip', [b('runixz80.tap')])
    write('runixz80-z80.zip', [(os.path.join(B, 'test.z80'), 'runixz80.z80')])
    write('runixz80-multitask-z80.zip', [b('runixz80-multitask.z80')])
    write('runixz80-c48-tzx.zip', [b('runixz80-c48.tzx')])
    tapes = [b(n) for n in ('c48-apps.tzx', 'c48-demos.tzx', 'c48-examples.tzx', 'c48-games.tzx',
                            'c48-multitask.tzx')]
    tapes += [(f, 'c48/' + os.path.basename(f)) for f in sorted(glob.glob(os.path.join(B, 'c48', '*.ta[p]')))]
    tapes += [(f, 'c48/' + os.path.basename(f)) for f in sorted(glob.glob(os.path.join(B, 'c48', '*.ssx')))]
    write('c48-tapes.zip', tapes)
    shots = [b('gallery.html')]
    shots += [(f, 'runix/' + os.path.basename(f)) for f in sorted(glob.glob(os.path.join(B, 'shots', '*.png')))]
    shots += [(f, 'vm/' + os.path.basename(f)) for f in sorted(glob.glob(os.path.join(B, 'shots-vm', '*.png')))]
    write('c48-screenshots.zip', shots)
    if logs:
        res = [(f, os.path.basename(f)) for f in sorted(glob.glob(os.path.join(logs, '*.txt')))]
        res += [(f, 'screens/' + os.path.basename(f)) for f in sorted(glob.glob(os.path.join(logs, '*.png')))]
        res.append(b('sizes.json'))
        write('test-results.zip', res)
    sj = os.path.join(ROOT, 'tools', 'bin', 'sjasmplus')
    lic = os.path.join(ROOT, '..', 'sjasm-src', 'LICENSE.md')
    if os.path.exists(sj) and os.path.exists(lic):
        write('build-tools-linux-x64.zip', [(sj, 'sjasmplus'), (lic, 'sjasmplus-LICENSE.md')])


if __name__ == '__main__':
    main(sys.argv[1:])

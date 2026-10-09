#!/usr/bin/env python3
"""Compile the C48 SDK corpus with the runix SDK and write cassette tapes.

  python3 tools/mktapes.py [--sdk DIR]

For every program in sdk/tests/runs.json (the ZX-UX C48 SDK's usr/src):
rcc -> build/c48/NAME.ssx (native code, or SSB1 bytecode when native code
would not fit), then rtap writes
  build/c48/NAME.tap              one program
  build/c48-<group>.tzx           the programs of a group (apps, demos, ...)
  build/c48-multitask.tzx         hanoi and queens8, to run together
  build/runixz80-c48.tzx          runix itself followed by every program
Boot runix, log in, play a tape and type /dev/cassette/NAME [args].
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'sdk'))
import rld    # noqa: E402
import rtap   # noqa: E402
from rcc import driver   # noqa: E402

GROUPS = (('apps', ('apps',)), ('games', ('games',)), ('demos', ('demos',)),
          ('examples', ('examples', 'sound', 'security')))


def main(argv):
    sdk = os.environ.get('C48SDK') or os.path.normpath(os.path.join(ROOT, '..', 'tuklusan', 'zx-ux-c48-sdk'))
    if argv[:1] == ['--sdk']:
        sdk = argv[1]
    runs = json.load(open(os.path.join(ROOT, 'sdk', 'tests', 'runs.json')))
    out = os.path.join(ROOT, 'build', 'c48')
    os.makedirs(out, exist_ok=True)
    progs = []
    for name, run in runs.items():
        if ':' in name:
            continue
        src = os.path.join(sdk, 'usr', 'src', run['dir'], run.get('src', name) + '.c')
        ssx = os.path.join(out, name + '.ssx')
        if driver.main([src, '-o', ssx]):
            raise SystemExit('rcc failed: %s' % name)
        data = open(ssx, 'rb').read()
        hdr, dat = rtap.records(data, name)
        rtap.write(os.path.join(out, name + '.tap'), b'', [(1000, hdr), (2000, dat)])
        progs.append((run['dir'], name, hdr, dat, len(data), rtap.need(data)))
    head = b'ZXTape!\x1a\x01\x14'
    for g, dirs in GROUPS:
        blocks = []
        t = ('runix C48 programs: %s' % g).encode()
        for d, name, hdr, dat, n, need in progs:
            if d in dirs:
                blocks += [(1000, hdr), (2000, dat)]
        rtap.write(os.path.join(ROOT, 'build', 'c48-%s.tzx' % g), head + bytes([0x30, len(t)]) + t, blocks)
    # hanoi and queens8 together: each draws one half of the screen; built
    # small (bytecode, stacks measured: the deepest recursion plus the VM's
    # 170 bytes for the kernel) so that both fit in memory at once
    blocks = []
    # (hanoi uses UDG slots 0-15 only: a 16-slot bank)
    for name, extra in (('hanoi', ['--stack', '400', '--udgs', '16']), ('queens8', ['--stack', '448'])):
        src = os.path.join(sdk, 'usr', 'src', 'demos', name + '.c')
        ssx = os.path.join(out, name + '-mt.ssx')
        if driver.main([src, '-o', ssx, '--bytecode'] + extra):
            raise SystemExit('rcc failed: %s' % name)
        hdr, dat = rtap.records(open(ssx, 'rb').read(), name)
        blocks += [(1000, hdr), (0 if name == 'hanoi' else 2000, dat)]   # pause 0: the tape stops
    t = b'runix C48 programs: hanoi and queens8 together'
    rtap.write(os.path.join(ROOT, 'build', 'c48-multitask.tzx'), head + bytes([0x30, len(t)]) + t, blocks)
    h, blocks = rtap.tzx_blocks(open(os.path.join(ROOT, 'build', 'runixz80.tzx'), 'rb').read())
    for d, name, hdr, dat, n, need in progs:
        blocks += [(1000, hdr), (2000, dat)]
    rtap.write(os.path.join(ROOT, 'build', 'runixz80-c48.tzx'), h, blocks)
    for d, name, hdr, dat, n, need in progs:
        print('%-9s %-11s %5d bytes, needs %5d' % (d, name, n, need))
    print('%d programs' % len(progs))


if __name__ == '__main__':
    main(sys.argv[1:])

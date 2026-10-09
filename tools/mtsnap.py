#!/usr/bin/env python3
"""A .z80 snapshot of ZX-UX with hanoi and queens8 running together.

  python3 tools/mtsnap.py [FRAMES]        -> build/ZX-UX-multitask.z80 (+ .png)

Boots from build/test.z80 (tools/t.sh), logs in, loads hanoi (&) and then
queens8 (&) from build/c48-multitask.tzx's programs (tools/mktapes.py) the
way a user would, runs FRAMES more frames (default 500: the early moves),
and writes the machine state.  Load the snapshot in any 48K emulator: both
programs carry on, the shell's prompt is on rows 21-22.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for d in ('tools', 'sdk', 'tests'):
    sys.path.insert(0, os.path.join(ROOT, d))
import rtap                                             # noqa: E402
import rvm                                              # noqa: E402
import suite                                            # noqa: E402
import zxrun                                            # noqa: E402
from skoolkit.simutils import get_state                 # noqa: E402
from skoolkit.snapshot import write_snapshot            # noqa: E402


def load(s, name, own, count):
    ssx = open(os.path.join(ROOT, 'build', 'c48', name + '-mt.ssx'), 'rb').read()
    s.zx.type('/dev/cassette/%s &\n' % name)
    s.zx.tr.edges = zxrun.tape_pulses(rtap.records(ssx, name), s.zx.sim.registers[25] + 350000)
    for _ in range(500):
        if bin(s.zx.mem[own]).count('1') >= count:
            return
        s.zx.run(10)
    raise SystemExit('%s did not start' % name)


def main(argv):
    frames = int(argv[0]) if argv else 500
    s = suite.Session(os.path.join(ROOT, 'build', 'test.z80'))
    s.login()
    own = suite.ksym('scrown')
    load(s, 'hanoi', own, 1)
    s.zx.run(100)
    s.zx.type('\n')                     # a prompt below the picture
    s.zx.run(100)
    load(s, 'queens8', own, 2)
    s.zx.run(frames)
    sim = s.zx.sim
    sim.tracer.outfe = getattr(sim.tracer, 'outfe', 0)
    if not hasattr(sim.tracer, 'border') or not isinstance(sim.tracer.border, (int, list)):
        sim.tracer.border = 0
    ram, regs, state, machine = get_state(sim)
    out = os.path.join(ROOT, 'build', 'ZX-UX-multitask.z80')
    if os.path.exists(out):
        os.remove(out)
    write_snapshot(out, ram, regs, state, '48K')
    rvm.write_png(bytes(s.zx.mem[0x4000:0x5B00]), out[:-4] + '.png', 0)
    print(out, os.path.getsize(out), 'scrown', bin(s.zx.mem[own]))


if __name__ == '__main__':
    main(sys.argv[1:])

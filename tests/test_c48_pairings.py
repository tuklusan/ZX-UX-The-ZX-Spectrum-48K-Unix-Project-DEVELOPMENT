"""Five concurrent cassette-program pairings on the actual ZX-UX Z80 kernel.

Run after an independent ROM tape boot has produced build/test.z80.
C48 inputs are the normal release SSX files, never alternate -mt copies.
"""
from __future__ import annotations
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import rtap
import suite

PAIRS = (('hanoi', 'queens8'), ('mobius', 'torus'),
         ('ball', 'hanoi'), ('ball', 'mobius'), ('ball', 'torus'))


def one_pair(snapshot, pair):
    # For BALL, load the longer-running companion first.  BALL otherwise
    # completes while the long cassette is still being loaded.
    ordered = tuple(reversed(pair)) if pair[0] == 'ball' else pair
    s = suite.Session(str(snapshot))
    s.login()
    for name in ordered:
        path = ROOT / 'dist/assets/c48-bin/ssx' / (name + '.ssx')
        if not path.is_file():
            raise AssertionError('Missing normal release image: ' + str(path))
        tape = rtap.records(path.read_bytes(), name)
        s.zx.type('/dev/cassette/%s &\n' % name)
        suite.run_past(s, suite.play(s, tape), 10)
        if suite.slot_named(s, name) is None:
            raise AssertionError('%s failed to load: \n%s' % (name, s.screen()))
    slots = [suite.slot_named(s, x) for x in ordered]
    if None in slots or len(set(slots)) != 2:
        raise AssertionError('both programs not concurrent: ' + s.status())
    if suite.kword(s, 'wlend') != 0:
        raise AssertionError('program window lent: ' + s.status())
    old = [suite.cpu_ticks(s, i) for i in slots]
    s.wait(35)
    new = [suite.cpu_ticks(s, i) for i in slots]
    delta = [((n - o) & 0xffff) for n, o in zip(new, old)]
    if not all(n > 0 for n in delta):
        raise AssertionError('both jobs did not get CPU time: %s, %s' % (delta, s.status()))
    if pair == ('hanoi', 'queens8'):
        if s.zx.mem[suite.ksym('scrown')].bit_count() != 2:
            raise AssertionError('Hanoi and Queens8 did not both own the screen')
        s.wait(2500)
        if 'FRAME FAIL' in s.screen() or 'not enough memory' in s.screen():
            raise AssertionError('Hanoi/Queens8 crashed: ' + s.screen())
        if not all(suite.slot_named(s, name) is not None for name in ordered):
            raise AssertionError('Hanoi/Queens8 ended prematurely: ' + s.status())
    return delta


def main():
    snap = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'build/test.z80'
    failures = 0
    for pair in PAIRS:
        try:
            delta = one_pair(snap, pair)
            print('PASS %-18s concurrent CPU ticks %s' % ('+'.join(pair), delta), flush=True)
        except Exception as exc:
            print('FAIL %-18s %s' % ('+'.join(pair), exc), flush=True)
            failures += 1
    print('%d failed out of %d' % (failures, len(PAIRS)), flush=True)
    return 1 if failures else 0

if __name__ == '__main__':
    raise SystemExit(main())

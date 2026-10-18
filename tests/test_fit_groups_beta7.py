"""Fresh-image, real SDK-VM checks for normal-name background pairs.

A 48K process pair must fit with an untouched resident shell and a
measurable emergency arena reserve in either launch order.  Compare
actual pixels and messages; a merely successful compiler is insufficient.
"""
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SDK = ROOT / 'release/dist/sdk/bin/py'
sys.path.insert(0, str(SDK))
from zxux import Session

TAPE = ROOT / 'release/dist/zx-ux/ZX-UX.tzx'
PROGRAMS = ROOT / 'release/dist/assets/c48-bin/ssx'
SYMS = (ROOT / 'release/build/src/unix.sym').read_text()
def address(name):
    m = re.search(r'^' + re.escape(name) + r': EQU 0x([0-9A-Fa-f]+)$', SYMS, re.M)
    assert m, 'freshly linked symbol missing: ' + name
    return int(m.group(1), 16)


def free_arena(session):
    start = address('AR0')
    end = session.word(address('a_top'))
    free = 0
    while start < end:
        length = session.word(start)
        assert 4 <= length <= 65530 and not (length & 1) and start + length <= end
        if session.m.mem[start + 2] == 0:
            free += length
        start += length
    assert start == end
    return free


class SelectedGroup(unittest.TestCase):
    def launch_pair(self, first, second):
        machine = Session(system=str(TAPE), cache=False)
        machine.boot()
        jobs = []
        for name in (first, second):
            data = (PROGRAMS / (name + '.ssx')).read_bytes()
            self.assertTrue(data.startswith(b'SSX1'))
            jobs.append(machine.launch(data, name, background=True))
        machine.run_until(lambda: all(j.started is not None for j in jobs),
                          1600, first + ' and ' + second)
        for _ in range(250):
            machine.step()
        self.assertTrue(all(j.ended is None and machine.slot_of(j.pid) is not None for j in jobs))
        self.assertGreaterEqual(free_arena(machine), 128)
        screen = machine.text()
        self.assertIn(first + ' ' if len(first) < 8 else first[:8], screen)
        self.assertIn(second + ' ' if len(second) < 8 else second[:8], screen)
        self.assertTrue(all(job.owned for job in jobs), 'each job must claim the screen')
        if {first, second} == {'hanoi', 'queens8'}:
            self.assertIn('TOWERS OF HANOI', screen)
            self.assertIn('QUEENS', screen)
            self.assertIn('FRAME GUARD OK', screen)
            self.assertIn('ROW', screen)
            self.assertIn('DISC', screen)
        else:
            # These two original full-screen pictures intentionally share the
            # display; the last scheduled painter can overwrite the title.
            self.assertTrue('TORUS REACTOR' in screen or 'MOBIUS R=48' in screen)
            self.assertIn('PARAMETRIC 3D' if 'TORUS REACTOR' in screen else 'ONE-SIDED', screen)
        machine.kb.type('cd /bin\n')
        for _ in range(150):
            machine.step()
        self.assertIn(machine.last_line(), ('#', '@'))
        self.assertGreaterEqual(free_arena(machine), 128)

    def test_hanoi_then_queens(self):
        self.launch_pair('hanoi', 'queens8')

    def test_queens_then_hanoi(self):
        self.launch_pair('queens8', 'hanoi')

    def test_mobius_then_torus(self):
        self.launch_pair('mobius', 'torus')

    def test_torus_then_mobius(self):
        self.launch_pair('torus', 'mobius')

    def test_no_duplicate_mt_shipments(self):
        import rtap
        ssx = {p.stem for p in PROGRAMS.glob('*.ssx')}
        tapes = ROOT / 'release/dist/assets/c48-bin/tzx'
        tzx = {p.stem for p in tapes.glob('*.tzx')}
        self.assertEqual(ssx, tzx)
        self.assertFalse(any(name.endswith('-mt') for name in ssx))
        self.assertTrue({'hanoi', 'queens8', 'mobius', 'torus'} <= ssx)
        for name in ('hanoi', 'queens8', 'mobius', 'torus'):
            data = (PROGRAMS / (name + '.ssx')).read_bytes()
            _, records = rtap.tzx_blocks((tapes / (name + '.tzx')).read_bytes())
            self.assertEqual(len(records), 2)
            self.assertEqual(records[1][1][1:-1], data)
            self.assertEqual(records[0][1][2:12], name.encode().ljust(10, b' '))


if __name__ == '__main__':
    unittest.main()

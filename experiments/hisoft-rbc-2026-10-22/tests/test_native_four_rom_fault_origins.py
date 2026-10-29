"""Witness four native ROM faults, without changing an instruction or game byte.

Negative diagnostics only. The BASIC line maps come from the actual linked
HiSoft line table in machine RAM, rather than assumptions about address order.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import rld
import rvm

GAMES = ROOT / 'src/bonus/60-programs'
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
KERNEL = ROOT / 'build/out/kernel.json'
CASES = (
    # Name, limit after boot, second start key index, failing BASIC line,
    # ROM ERR_NR (zero-based), invalid PRINT-AT coordinate (if applicable).
    ('03-tug-of-war', 650, None, 7020, 3, None),
    ('43-dogfight', 1030, None, 1040, 10, (255, 7)),
    ('47-exocet', 1140, None, 110, 10, (32, 13)),
    ('28-dam-busters', 4660, 350, 125, 10, (6, 255)),
)
READY = all(p.is_file() for p in (ROM, SYSTEM, FROZEN, KERNEL))


def source_line_table(machine, basic):
    """Find the original relocated HiSoft line/address pairs in real RAM."""
    mem = machine.mem
    lines = {int(m[1]) for line in basic.decode('ascii').splitlines()
             if (m := re.match(r'\s*(\d+)\s+', line))}
    first = min(lines)
    second = sorted(lines)[1]
    def word(a):
        return mem[a] | mem[a + 1] << 8
    candidates = []
    for start in range(0x8000, 0xff00):
        if word(start) != first or word(start + 4) != second:
            continue
        pairs = []
        for k in range(min(200, (65536 - start) // 4)):
            pos = start + 4 * k
            line, pc = word(pos), word(pos + 2)
            if line == 65535:
                break
            if line not in lines or not 0xc000 <= pc < 0xffc0:
                break
            pairs.append((line, pc))
        if len(pairs) >= 40:
            candidates.append(pairs)
    if len(candidates) != 1:
        raise AssertionError('original native line table not uniquely identified')
    return candidates[0]


def source_for_pc(table, pc):
    before = [(addr, line) for line, addr in table if addr <= pc]
    if not before:
        raise AssertionError(f'no original BASIC line for PC {pc:#06x}')
    return max(before)[1]


@unittest.skipUnless(READY, 'the original kernel, 48K ROM and game binaries are needed')
class FourOriginalRomFaultOrigins(unittest.TestCase):
    def test_rom_faults_and_original_source_line_witnesses(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        syms = json.loads(KERNEL.read_text())['symbols']
        self.assertEqual(syms['rom_error'], 0x6060)
        self.assertEqual(syms['panic'], 0x6048)
        for name, limit, second_key, expected_line, error, bad_at in CASES:
            with self.subTest(game=name):
                root = GAMES / name
                paths = (root / 'BASIC' / f'{name}.bas',
                         root / 'BASIC' / f'{name}.tzx',
                         root / 'bin' / f'{name}.ssx', ROM)
                originals = tuple(p.read_bytes() for p in paths)
                parsed = rld.parse_ssx(originals[2])
                self.assertLessEqual(max(len(originals[2]),
                                         len(parsed['image']) + parsed['bss'] +
                                         parsed['stack']), 14000)
                run = rvm.run_kernel(paths[2], keys='', frames=400, system=SYSTEM)
                self.assertIsNotNone(run.fg.started)
                self.assertTrue(run.session.owns_screen(run.fg.pid))
                m = run.session.m
                line_table = source_line_table(m, originals[0])
                events = []
                def word(a):
                    return m.mem[a] | m.mem[(a + 1) & 65535] << 8
                def print_at(machine):
                    c = machine.cpu
                    if c.b > 21 or c.c > 31:
                        sp = c.sp
                        upper = max(a for _, a in line_table)
                        caller = next((word(sp + off) for off in
                                       (4, 6, 8, 10, 12, 14, 16)
                                       if 0xc800 <= word(sp + off) <= upper), None)
                        events.append(('at', c.b, c.c, caller,
                                       source_for_pc(line_table, caller)
                                       if caller is not None else None))
                    return False
                def let(machine):
                    c = machine.cpu
                    if (c.b << 8 | c.c) > 14000:
                        caller = word(c.sp)
                        events.append(('string', (c.b << 8) | c.c, caller,
                                       source_for_pc(line_table, caller)))
                    return False
                def out_of_memory(machine):
                    events.append(('oom', machine.cpu.pc))
                    return False
                def rom_error(machine):
                    events.append(('rom_error', machine.cpu.pc,
                                   machine.mem[0x5c3a]))
                    return False
                for addr, callback in ((0x0a9b, print_at), (0x2b7f, let),
                                       (0x1f15, out_of_memory),
                                       (syms['rom_error'], rom_error)):
                    self.assertNotIn(addr, m.hooks)
                    m.hooks[addr] = callback
                run.session.kb.type('a')
                for frame in range(limit):
                    if frame == second_key:
                        run.session.kb.type('a')
                    run.frame()
                    if any(e[0] == 'rom_error' for e in events):
                        break
                faults = [e for e in events if e[0] == 'rom_error']
                self.assertEqual(len(faults), 1, f'{name}: no proven ROM error')
                self.assertEqual(faults[0][1:], (0x6060, error))
                if bad_at is None:
                    self.assertIn(('oom', 0x1f15), events)
                    candidates = [e for e in events if e[0] == 'string']
                    self.assertIn(('string', 0xc80c, 0xde6c, expected_line),
                                  candidates)
                else:
                    candidates = [e for e in events if e[0] == 'at'
                                  and e[1:3] == bad_at]
                    self.assertTrue(candidates, f'{name}: invalid AT not observed')
                    self.assertEqual(candidates[-1][4], expected_line)
                for _ in range(30):
                    run.frame()
                self.assertFalse(run.session.owns_screen(run.fg.pid))
                self.assertIsNone(run.fg.ended)
                self.assertFalse(m.cpu.iff1)
                self.assertEqual(tuple(p.read_bytes() for p in paths), originals)
                self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
                print(name, 'BASIC', expected_line, 'ERR_NR', error,
                      'ROM', hex(faults[0][1]), 'witness', candidates[-1],
                      'ssx_sha256', sha256(originals[2]).hexdigest())


if __name__ == '__main__':
    unittest.main()

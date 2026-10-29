"""Original 3 TZX sources versus unmodified ZX-UX native PRINT AT faults.

Read-only bus and instruction probes: an observation is not game completion.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'), str(Path(__file__).parent)]
import rld
import rvm
from test_native_four_rom_fault_origins import source_for_pc, source_line_table

TOOL = ROOT / 'build/tools/zx-tzx2bas.py'
SPEC = importlib.util.spec_from_file_location('original_tzx_lister', TOOL)
LISTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LISTER)
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
KERNEL = ROOT / 'build/out/kernel.json'
CASES = (
    ('43-dogfight', 1040, (255, 7), (0, 8), 1030, None),
    ('47-exocet', 110, (32, 13), (10, 0), 1140, None),
    ('28-dam-busters', 125, (6, 255), (6, 0), 4660, 350),
)
READY = all(p.is_file() for p in (TOOL, ROM, SYSTEM, FROZEN, KERNEL))


def sources(name):
    folder = ROOT / 'src/bonus/60-programs' / name
    return (folder / 'BASIC' / (name + '.bas'),
            folder / 'BASIC' / (name + '.tzx'),
            folder / 'bin' / (name + '.ssx'))


def word(mem, addr):
    return mem[addr & 65535] | mem[(addr + 1) & 65535] << 8


@unittest.skipUnless(READY, 'original ZX-UX ROM, tape and kernel required')
class OriginalTzxNativeAtOrigins(unittest.TestCase):
    def test_independent_all_lines_from_three_tapes_match_bas(self):
        for name, line, _, _, _, _ in CASES:
            with self.subTest(game=name):
                bas, tzx, ssx = sources(name)
                before = (bas.read_bytes(), tzx.read_bytes(), ssx.read_bytes())
                programs = list(LISTER.basic_programs(before[1]))
                self.assertEqual(len(programs), 1)
                original = before[0].decode('ascii').splitlines()
                decoded = LISTER.listing(before[1]).splitlines()
                self.assertEqual(len(original), len(decoded))
                self.assertEqual([x.strip() for x in original],
                                 [x.strip() for x in decoded])
                self.assertTrue(any(int(x.split()[0]) == line for x in decoded))
                self.assertEqual(before, (bas.read_bytes(), tzx.read_bytes(), ssx.read_bytes()))

    def test_exocet_kernel_tapq_byte_enters_print_string(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        name = '47-exocet'
        paths = (*sources(name), ROM)
        before = tuple(p.read_bytes() for p in paths)
        symbols = json.loads(KERNEL.read_text())['symbols']
        self.assertEqual(symbols['tapq'], 0x5dcd)
        self.assertEqual(symbols['isr.c9'], 0x60e0)
        run = rvm.run_kernel(paths[2], keys='', frames=400, system=SYSTEM)
        m = run.session.m
        table = source_line_table(m, before[0])
        self.assertEqual(source_for_pc(table, 0xcfa6), 1250)
        self.assertEqual(source_for_pc(table, 0xc91f), 110)
        writes = []
        emitted = []
        invalid_at = []
        native_write = m.cpu.write_byte
        def watch_write(address, value):
            if address in (0x5dcd, 0xe5df) and value != m.mem[address]:
                c = m.cpu
                if len(writes) < 160:
                    writes.append((address, m.mem[address], value, c.pc,
                                   c.h << 8 | c.l, c.d << 8 | c.e,
                                   word(m.mem, c.sp)))
            return native_write(address, value)
        def watch_output(machine):
            c = machine.cpu
            if c.a == 0x16 and word(machine.mem, c.sp) == 0x2043:
                emitted.append((c.a, (c.d << 8 | c.e) - 1))
            return False
        def watch_at(machine):
            c = machine.cpu
            if c.b > 21 or c.c > 31:
                invalid_at.append((c.b, c.c))
            return False
        m.cpu.write_byte = watch_write  # forwards every write unchanged
        m.hooks[0x10] = watch_output
        m.hooks[0x0a9b] = watch_at
        run.session.kb.type('a')
        for _ in range(1140):
            run.frame()
            if m.mem[0x5c3a] == 10:
                break
        self.assertEqual(m.mem[0x5c3a], 10)
        self.assertIn((32, 13), invalid_at)
        self.assertIn((0x16, 0xe5df), emitted)
        # ROM's temporary string work area overlaps a kernel-owned timer.
        self.assertTrue(any(a == 0x5dcd and old == 0x20 and new == 0x1f
                            and pc == 0x60e8 for a, old, new, pc, _, _, _ in writes))
        self.assertTrue(any(a == 0xe5df and old == 0 and new == 0x20
                            and pc == 0xdb1c and src == 0x5dcd and caller == 0xcfa6
                            for a, old, new, pc, src, _, caller in writes))
        # Preserve all originals, observe only. No ROM, kernel, SSX or BASIC patch.
        self.assertEqual(tuple(p.read_bytes() for p in paths), before)
        self.assertFalse(run.session.owns_screen(run.fg.pid))
        self.assertIsNone(run.fg.ended)
        print(name, 'tapq', hex(symbols['tapq']), 'ROM copy', hex(0x35b7),
              'runtime copy', hex(0xdb1c), 'output', (0x16, 0xe5df),
              'invalid_at', (32, 13))


if __name__ == '__main__':
    unittest.main()

"""Reproduce three original published game ROM panics under the real ZX-UX.

This is a negative diagnostic, not gameplay success or an emulator fix.
Read-only CPU hooks observe real linked kernel entry addresses and never
change the program, memory, system tape, ROM, or execution path.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import rld
import rvm

GAMES = ROOT / 'src/bonus/60-programs'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
KERNEL = ROOT / 'build/out/kernel.json'
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
CASES = (
    ('03-tug-of-war', 'a', 800),
    ('43-dogfight', 'a', 1450),
    ('47-exocet', 'a', 1500),
)
READY = all(p.is_file() for p in (SYSTEM, FROZEN, KERNEL, ROM))


@unittest.skipUnless(READY, 'reconstructed ZX-UX and authentic ROM required')
class NativeUnfinishedRomPanicDiagnostics(unittest.TestCase):
    def test_originals_reach_kernel_rom_error_not_round_completion(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        metadata = json.loads(KERNEL.read_text())
        symbols = metadata['symbols']
        self.assertEqual(symbols['panic'], 0x6048)
        self.assertEqual(symbols['rom_error'], 0x6060)
        source = (ROOT / 'src/zx-ux/unix.asm').read_text()
        self.assertIn('rom_error:                      ; RST 8 from a ROM routine', source)
        self.assertIn('ld (scrown),a', source)
        for name, start_key, frame_limit in CASES:
            with self.subTest(name=name):
                game = GAMES / name
                paths = (game / 'BASIC' / (name + '.bas'),
                         game / 'BASIC' / (name + '.tzx'),
                         game / 'bin' / (name + '.ssx'), ROM)
                originals = tuple(p.read_bytes() for p in paths)
                native = originals[2]
                linked = rld.parse_ssx(native)
                self.assertEqual(linked['entry'], 0)
                self.assertLessEqual(max(len(native), len(linked['image']) +
                                         linked['bss'] + linked['stack']), 14000)
                run = rvm.run_kernel(paths[2], keys='', frames=400, system=SYSTEM)
                self.assertIsNotNone(run.fg.started)
                self.assertIsNone(run.fg.ended)
                self.assertTrue(run.session.owns_screen(run.fg.pid))
                hits = []
                for kind in ('rom_error', 'panic'):
                    address = symbols[kind]
                    self.assertNotIn(address, run.session.m.hooks)
                    def observe(machine, label=kind):
                        cpu = machine.cpu
                        hits.append((label, machine.frame, cpu.pc,
                                     cpu.sp, cpu.a, (cpu.h << 8) | cpu.l))
                        return False  # perform the original instruction
                    run.session.m.hooks[address] = observe
                run.session.kb.type(start_key)
                for _ in range(frame_limit):
                    run.frame()
                    if len(hits) >= 2:
                        break
                self.assertEqual([x[0] for x in hits[:2]],
                                 ['rom_error', 'panic'],
                                 'no verified ROM-error -> kernel-panic sequence')
                self.assertLess(hits[0][1], hits[1][1] + 1)
                self.assertEqual(hits[0][2], symbols['rom_error'])
                self.assertEqual(hits[1][2], symbols['panic'])
                for _ in range(35):
                    run.frame()
                self.assertEqual(run.session.m.cpu.pc, symbols['panic.h'] + 1)
                self.assertFalse(run.session.m.cpu.iff1)
                self.assertFalse(run.session.owns_screen(run.fg.pid))
                self.assertIsNone(run.fg.ended)
                self.assertEqual(tuple(p.read_bytes() for p in paths), originals)
                self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
                print(name, 'ROM error at frame', hits[0][1],
                      'panic at frame', hits[1][1],
                      'SHA256', hashlib.sha256(native).hexdigest())


if __name__ == '__main__':
    unittest.main()

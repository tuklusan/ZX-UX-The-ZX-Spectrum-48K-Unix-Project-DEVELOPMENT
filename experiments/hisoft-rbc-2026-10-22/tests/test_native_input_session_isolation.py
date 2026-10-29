"""Real-kernel isolation regression for the experimental source-owned INPUT.

This does not approve the experimental editor for the delivered RBC path.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'experiments/hisoft-rbc-2026-10-22/tests'),
                str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'),
                str(ROOT / 'src/zx-ux-sdk')]
from native_rbc_cli import compile_native
from test_native_input_bridge_candidate import link_candidate
import rld
import rvm

CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (
    CHECKPOINT / 'rbc.py', CHECKPOINT / 'font32.bin', FRONTEND / 'compiler.py',
    TAPE, ROM, SYSTEM, FROZEN))

PROGRAM = ('10 REM : OPEN #\n20 INPUT A$\n'
           '30 POKE 22528,LEN A$+30\n40 STOP\n')
PROTECTED = (0x5c36, 0x5c37, 0x5c7b, 0x5c7c,
             0x5c6a, 0x5c39, 0x5c8d, 0x5c8e, 0x5c8f, 0x5c90)


@unittest.skipUnless(READY, 'requires original HiSoft compiler and ZX-UX system')
class NativeInputSessionIsolation(unittest.TestCase):
    def test_two_separate_keyboard_input_processes_return_to_same_shell(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        with tempfile.TemporaryDirectory(prefix='rbc-input-session-') as folder:
            bas = Path(folder) / 'input-session.bas'
            ssx = Path(folder) / 'input-session.ssx'
            bas.write_text(PROGRAM, encoding='ascii')
            asm, obj, untouched, report = compile_native(
                bas, CHECKPOINT, FRONTEND, TAPE, ROM, input_backend='rom')
            self.assertTrue(obj.startswith(b'SSO1'))
            self.assertTrue(report['native_and_legacy_ssx_byte_identical'])
            self.assertTrue(report['native_three_base_source_verified'])
            self.assertFalse(report['optimizer_used'])
            candidate = link_candidate(asm)
            self.assertNotEqual(candidate, untouched)
            image = rld.parse_ssx(candidate)
            self.assertLessEqual(max(len(candidate), len(image['image']) +
                                     image['bss'] + image['stack']), 14000)
            ssx.write_bytes(candidate)

            first = rvm.run_kernel(ssx, keys='{WAIT 200}alpha{ENTER}',
                                   frames=1200, system=SYSTEM)
            self.assertEqual(first.why, 'exit', first.summary())
            self.assertEqual(first.fg.status, 0)
            self.assertEqual(first.fg.exit_picture[0][6144], 35)
            session = first.session
            session.wait_prompt(1500)
            self.assertEqual(session.last_line(), '#')
            self.assertIsNone(session.slot_of(first.fg.pid))
            self.assertFalse(session.owns_screen(first.fg.pid))
            state = bytes(session.m.mem[x] for x in PROTECTED)
            self.assertEqual(session.word(0x5c36), 0x3c00)

            second = session.launch(candidate, 'input2')
            session.kb.type('xy\n')
            for _ in range(1800):
                session.step()
                if second.ended is not None:
                    break
            else:
                self.fail('second INPUT program did not exit')
            self.assertIsNotNone(second.started)
            self.assertEqual(second.status, 0)
            self.assertEqual(second.exit_picture[0][6144], 32)
            self.assertIsNone(session.slot_of(second.pid))
            self.assertFalse(session.owns_screen(second.pid))
            session.wait_prompt(1500)
            self.assertEqual(session.last_line(), '#')
            self.assertEqual(bytes(session.m.mem[x] for x in PROTECTED), state)
            count = session.syscalls
            session.kb.type('\n')
            session.wait_prompt(1500)
            self.assertGreater(session.syscalls, count)


if __name__ == '__main__':
    unittest.main()

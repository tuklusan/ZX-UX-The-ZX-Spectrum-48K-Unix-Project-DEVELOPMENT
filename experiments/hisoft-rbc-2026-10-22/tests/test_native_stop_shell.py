"""Real original HiSoft -> pre-link Z80 -> ras/rld -> ZX-UX STOP lifecycle.

These are original numbered ASCII test fixtures, not game replacements. No
C48 backend, source patch, SSX edit, or synthetic emulator result is used.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
from native_rbc_cli import compile_native
import rld
import rvm

CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (CHECKPOINT / 'rbc.py',
    CHECKPOINT / 'font32.bin', FRONTEND / 'compiler.py', TAPE, ROM,
    SYSTEM, FROZEN))

STOP_GOSUB = (
    '10 REM : OPEN #\n'
    '20 LET A=0\n'
    '30 GO SUB 100\n'
    '40 IF A=3 THEN GO TO 200\n'
    '50 GO TO 300\n'
    '100 LET A=A+3\n'
    '110 RETURN\n'
    '200 POKE 22528,34: PAUSE 30: STOP\n'
    '300 POKE 22528,68: PAUSE 30: STOP\n'
)


@unittest.skipUnless(READY, 'verified original HiSoft inputs and built ZX-UX required')
class NativeStopShell(unittest.TestCase):
    def test_stop_gosub_three_base_relocation_shell_and_second_process(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes(),
                         'original ZX-UX release tape must remain unchanged')
        with tempfile.TemporaryDirectory(prefix='rbc-native-stop-') as tmp:
            source = Path(tmp) / 'native-stop-gosub.bas'
            linked = Path(tmp) / 'native-stop-gosub.ssx'
            source.write_text(STOP_GOSUB, encoding='ascii')
            asm, obj, ssx, proof = compile_native(
                source, CHECKPOINT, FRONTEND, TAPE, ROM)
            self.assertIn('rbc_wrapper_hisoft_entry:', asm)
            self.assertIn('    section data\n', asm)
            self.assertTrue(obj.startswith(b'SSO1'))
            self.assertTrue(proof['native_three_base_source_verified'])
            self.assertTrue(proof['native_and_legacy_ssx_byte_identical'])
            self.assertFalse(proof['optimizer_used'])
            header = rld.parse_ssx(ssx)
            self.assertEqual(header['entry'], 0)
            self.assertEqual(header['bss'], 19)
            self.assertLessEqual(max(len(ssx), proof['total']), 14000)
            linked.write_bytes(ssx)

            first = rvm.run_kernel(linked, frames=1200, system=SYSTEM)
            self.assertEqual(first.why, 'exit', first.summary())
            self.assertEqual(first.fg.status, 0)
            self.assertIsNotNone(first.fg.started)
            self.assertIsNotNone(first.fg.ended)
            self.assertEqual(first.fg.exit_picture[0][6144], 34,
                             'GO SUB / IF must take the verified STOP path')
            session = first.session
            self.assertIsNone(session.slot_of(first.fg.pid))
            self.assertFalse(session.owns_screen(first.fg.pid))
            session.wait_prompt(1500)
            self.assertEqual(session.last_line(), '#')
            # The original ROM CHARS pointer, not a process-owned font.
            self.assertEqual(session.word(0x5c36), 0x3c00)
            protected = (0x5c36, 0x5c37, 0x5c7b, 0x5c7c, 0x5c6a,
                         0x5c39, 0x5c8d, 0x5c8e, 0x5c8f, 0x5c90)
            after_first = bytes(session.m.mem[n] for n in protected)

            # Launch again in the same kernel: confirms STOP returned to a
            # working shell and did not contaminate the next process.
            second = session.launch(ssx, 'stop2')
            for _ in range(1600):
                session.step()
                if second.ended is not None:
                    break
            else:
                self.fail('second native process did not return to ZX-UX shell')
            self.assertIsNotNone(second.started)
            self.assertEqual(second.status, 0)
            self.assertIsNone(session.slot_of(second.pid))
            self.assertFalse(session.owns_screen(second.pid))
            self.assertEqual(second.exit_picture[0][6144], 34)
            session.wait_prompt(1500)
            self.assertEqual(session.last_line(), '#')
            self.assertEqual(bytes(session.m.mem[n] for n in protected), after_first)
            # Real shell keyboard input remains accepted after both exits.
            count = session.syscalls
            session.kb.type('\n')
            session.wait_prompt(1500)
            self.assertGreater(session.syscalls, count)

    def test_native_natural_completion_restores_shell(self):
        with tempfile.TemporaryDirectory(prefix='rbc-native-completion-') as tmp:
            src = Path(tmp) / 'natural-end.bas'
            target = Path(tmp) / 'natural-end.ssx'
            src.write_text('10 REM : OPEN #\n20 LET A=1\n'
                           '30 PRINT "NATIVE COMPLETION"\n', encoding='ascii')
            _, obj, ssx, report = compile_native(
                src, CHECKPOINT, FRONTEND, TAPE, ROM)
            self.assertTrue(obj.startswith(b'SSO1'))
            self.assertTrue(report['native_and_legacy_ssx_byte_identical'])
            self.assertLessEqual(max(len(ssx), report['total']), 14000)
            target.write_bytes(ssx)
            outcome = rvm.run_kernel(target, frames=1200, system=SYSTEM)
            self.assertEqual(outcome.why, 'exit', outcome.summary())
            self.assertEqual(outcome.fg.status, 0)
            self.assertIsNone(outcome.session.slot_of(outcome.fg.pid))
            self.assertFalse(outcome.session.owns_screen(outcome.fg.pid))
            outcome.session.wait_prompt(1500)
            self.assertEqual(outcome.session.last_line(), '#')
            self.assertEqual(outcome.session.word(0x5c36), 0x3c00)

    def test_zero_bss_stkend_end_marker_stops_and_returns_to_shell(self):
        # HiSoft emits LD HL,one-past-image; LD (STKEND),HL. This is
        # a pointer sentinel, not a writable BSS byte or a generic exception.
        with tempfile.TemporaryDirectory(prefix='rbc-zero-bss-stop-') as tmp:
            source = Path(tmp) / 'zero-bss-stop.bas'
            target = Path(tmp) / 'zero-bss-stop.ssx'
            source.write_text('10 REM : OPEN #\n20 STOP\n', encoding='ascii')
            asm, obj, ssx, proof = compile_native(
                source, CHECKPOINT, FRONTEND, TAPE, ROM)
            self.assertTrue(obj.startswith(b'SSO1'))
            self.assertTrue(proof['native_three_base_source_verified'])
            self.assertTrue(proof['native_and_legacy_ssx_byte_identical'])
            self.assertFalse(proof['optimizer_used'])
            self.assertEqual(rld.parse_ssx(ssx)['bss'], 0)
            self.assertIn('source_0049:', asm)
            self.assertLessEqual(max(len(ssx), proof['total']), 14000)
            target.write_bytes(ssx)
            first = rvm.run_kernel(target, frames=1200, system=SYSTEM)
            self.assertEqual(first.why, 'exit', first.summary())
            self.assertEqual(first.fg.status, 0)
            session = first.session
            self.assertIsNone(session.slot_of(first.fg.pid))
            self.assertFalse(session.owns_screen(first.fg.pid))
            session.wait_prompt(1500)
            self.assertEqual(session.last_line(), '#')
            self.assertEqual(session.word(0x5c36), 0x3c00)
            after_first = bytes(session.m.mem[n] for n in
                (0x5c36, 0x5c37, 0x5c7b, 0x5c7c, 0x5c6a,
                 0x5c39, 0x5c8d, 0x5c8e, 0x5c8f, 0x5c90))
            second = session.launch(ssx, 'stop2')
            for _ in range(1600):
                session.step()
                if second.ended is not None:
                    break
            else:
                self.fail('second zero-BSS STOP did not exit')
            self.assertEqual(second.status, 0)
            self.assertIsNone(session.slot_of(second.pid))
            self.assertFalse(session.owns_screen(second.pid))
            session.wait_prompt(1500)
            self.assertEqual(session.last_line(), '#')
            self.assertEqual(bytes(session.m.mem[n] for n in
                (0x5c36, 0x5c37, 0x5c7b, 0x5c7c, 0x5c6a,
                 0x5c39, 0x5c8d, 0x5c8e, 0x5c8f, 0x5c90)), after_first)
            count = session.syscalls
            session.kb.type('\n')
            session.wait_prompt(1500)
            self.assertGreater(session.syscalls, count)


if __name__ == '__main__':
    unittest.main()

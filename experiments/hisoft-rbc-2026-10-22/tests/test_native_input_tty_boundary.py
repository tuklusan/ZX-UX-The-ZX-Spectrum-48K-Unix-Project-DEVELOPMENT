"""Witness the kernel tty line limit in the experimental INPUT bridge.

The original Spectrum ROM editor accepts a different input capacity. This
experiment must not be mistaken for production Sinclair INPUT equivalence.
"""
from __future__ import annotations

import os
import json
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
KERNEL_CONSTANTS = ROOT / 'src/zx-ux/const.inc'
KERNEL_SYMBOLS = ROOT / 'build/out/kernel.json'
READY = all(p.is_file() for p in (
    CHECKPOINT / 'rbc.py', CHECKPOINT / 'font32.bin', FRONTEND / 'compiler.py',
    TAPE, ROM, SYSTEM, FROZEN, KERNEL_CONSTANTS, KERNEL_SYMBOLS))


@unittest.skipUnless(READY, 'verified 48K compiler, kernel and ROM required')
class NativeInputTtyBoundary(unittest.TestCase):
    def test_canonical_tty_line_is_limited_to_79_characters(self):
        # Kernel dev.asm checks TTYBSZ-1 before appending a character,
        # then adds ENTER as byte 80. This truncates longer keyboard lines.
        self.assertIn('TTYBSZ  equ 80', KERNEL_CONSTANTS.read_text())
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        lowk = json.loads(KERNEL_SYMBOLS.read_text())['symbols']['LOWK']
        self.assertEqual(lowk, 0x5d98)
        with tempfile.TemporaryDirectory(prefix='rbc-tty-boundary-') as temp:
            original = Path(temp) / 'tty-boundary.bas'
            native = Path(temp) / 'tty-boundary.ssx'
            original.write_text('10 REM : OPEN #\n20 INPUT A$\n'
                                '30 POKE 22528,LEN A$+20\n40 STOP\n',
                                encoding='ascii')
            source, obj, reference, proof = compile_native(
                original, CHECKPOINT, FRONTEND, TAPE, ROM, input_backend='rom')
            self.assertTrue(obj.startswith(b'SSO1'))
            self.assertTrue(proof['native_three_base_source_verified'])
            self.assertTrue(proof['native_and_legacy_ssx_byte_identical'])
            self.assertFalse(proof['optimizer_used'])
            changed = link_candidate(source)
            self.assertNotEqual(changed, reference)
            image = rld.parse_ssx(changed)
            self.assertLessEqual(max(len(changed), len(image['image']) +
                                     image['bss'] + image['stack']), 14000)
            native.write_bytes(changed)
            for characters, readback in ((25, 25), (79, 79),
                                         (80, 79), (200, 79)):
                with self.subTest(chars=characters):
                    options = rvm.Options()
                    options.prog = str(native)
                    options.system = SYSTEM
                    options.keys = '{WAIT 200}' + 'c' * characters + '{ENTER}'
                    options.frames = 3000
                    case = rvm.Runner(options)
                    case.start()
                    stkend = []

                    def sample(_frame):
                        session = case.session
                        if (case.fg.started is not None and
                                case.fg.ended is None and
                                session.owns_screen(case.fg.pid)):
                            stkend.append(session.word(0x5c65))

                    case.session.frame_hooks.append(sample)
                    for _ in range(options.frames + 3000):
                        case.frame()
                        why = case.check(options.frames)
                        if why:
                            case.why = why
                            break
                    self.assertEqual(case.why, 'exit', case.summary())
                    self.assertEqual(case.fg.status, 0)
                    self.assertEqual(case.fg.exit_picture[0][6144], 20 + readback)
                    self.assertTrue(stkend, 'ROM workspace was not observed')
                    self.assertGreaterEqual(min(stkend), 0x5d40)
                    self.assertLess(max(stkend), lowk,
                                    'ROM edit workspace must not overwrite low kernel')
                    case.session.wait_prompt(1500)
                    self.assertEqual(case.session.last_line(), '#')
                    self.assertIsNone(case.session.slot_of(case.fg.pid))
                    self.assertFalse(case.session.owns_screen(case.fg.pid))


if __name__ == '__main__':
    unittest.main()

"""Source-only ZX-UX INPUT integration: strict token gate and real Z80 proof.

Deliberately opt-in: full Sinclair ROM editing has not passed. Never alter
published BAS/TZX/SSX or hide a difference from the verified HiSoft baseline.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'),
                str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'),
                str(ROOT / 'experiments/hisoft-rbc-2026-10-22/tests')]
import rld
import rvm
from native_rbc_cli import _has_input_token, compile_native
from native_input_source import assemble_input_source
from native_input_raw_candidate import assemble_candidate
from basic_listing import encode_strict_listing

CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (CHECKPOINT / 'rbc.py',
    CHECKPOINT / 'font32.bin', FRONTEND / 'compiler.py', TAPE, ROM,
    SYSTEM, FROZEN))


class InputTokenGate(unittest.TestCase):
    def test_quoted_and_rem_input_are_inert(self):
        source = '10 REM INPUT A$\n20 PRINT "INPUT"\n30 STOP\n'
        self.assertFalse(_has_input_token(encode_strict_listing(source)))
        self.assertTrue(_has_input_token(encode_strict_listing(
            '10 REM INPUT A$\n20 INPUT A$\n30 STOP\n')))

    def test_truncated_tokens_refused(self):
        for damaged in (b'\x00', b'\x00\x0a\x01\x00', b'\x00\x0a\xff\xff'):
            with self.subTest(data=damaged):
                with self.assertRaisesRegex(ValueError, 'truncated'):
                    _has_input_token(damaged)

    def test_missing_source_witness_refused(self):
        with self.assertRaisesRegex(ValueError, 'not independently witnessed'):
            assemble_input_source('    call 0x0f2c\n', stack=384, maximum=14000)


@unittest.skipUnless(READY, 'checked HiSoft/Z80/ZX-UX inputs unavailable')
class NativeInputSourceCompiler(unittest.TestCase):
    def test_optin_real_48k_numeric_string_delete_and_shell(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        program = ('10 REM : OPEN #\n20 INPUT A$\n'
                   '30 POKE 22528,LEN A$+20\n40 STOP\n')
        with tempfile.TemporaryDirectory(prefix='rbc-input-stage-') as tmp:
            bas = Path(tmp) / 'input.bas'
            output = Path(tmp) / 'input.ssx'
            bas.write_text(program, encoding='ascii')
            asm, _, legacy, original = compile_native(
                bas, CHECKPOINT, FRONTEND, TAPE, ROM)
            new_source, obj, result, proof = compile_native(
                bas, CHECKPOINT, FRONTEND, TAPE, ROM, input_backend='zxux')
            self.assertNotEqual(result, legacy)
            self.assertTrue(original['native_and_legacy_ssx_byte_identical'])
            self.assertFalse(proof['native_and_legacy_ssx_byte_identical'])
            self.assertTrue(proof['native_three_base_source_verified'])
            self.assertTrue(proof['input_source_bridge_three_base_verified'])
            self.assertFalse(proof['optimizer_used'])
            self.assertEqual(proof['input_backend'], 'zxux')
            self.assertEqual(result, assemble_candidate(asm))
            self.assertTrue(obj.startswith(b'SSO1'))
            linked = rld.parse_ssx(result)
            self.assertEqual(linked['entry'], 0)
            self.assertLessEqual(max(len(result), len(linked['image']) +
                                     linked['bss'] + linked['stack']), 14000)
            self.assertIn('rbc_raw_test_input:', new_source)
            output.write_bytes(result)
            for keys, value in (('ab{DELETE}cd', 23), ('', 20), ('xyz', 23)):
                with self.subTest(keys=keys):
                    run = rvm.run_kernel(output,
                        keys='{WAIT 200}' + keys + '{ENTER}',
                        frames=1400, system=SYSTEM)
                    self.assertEqual(run.why, 'exit', run.summary())
                    self.assertEqual(run.fg.status, 0)
                    self.assertEqual(run.fg.exit_picture[0][6144], value)
                    run.session.wait_prompt(1500)
                    self.assertEqual(run.session.last_line(), '#')
                    self.assertFalse(run.session.owns_screen(run.fg.pid))


if __name__ == '__main__':
    unittest.main()

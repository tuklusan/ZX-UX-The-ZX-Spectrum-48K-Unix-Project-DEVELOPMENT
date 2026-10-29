"""Source-only ZX-UX INPUT integration: strict token gate and real Z80 proof.

The default compiler uses bounded ZX-UX INPUT source. Explicit HiSoft ROM
comparison remains byte exact. Full non-INPUT ROM editor parity is not claimed.
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
                bas, CHECKPOINT, FRONTEND, TAPE, ROM, input_backend='rom')
            new_source, obj, result, proof = compile_native(
                bas, CHECKPOINT, FRONTEND, TAPE, ROM, input_backend='zxux')
            self.assertNotEqual(result, legacy)
            self.assertTrue(original['native_and_legacy_ssx_byte_identical'])
            self.assertFalse(proof['native_and_legacy_ssx_byte_identical'])
            self.assertTrue(proof['native_three_base_source_verified'])
            self.assertTrue(proof['input_source_bridge_three_base_verified'])
            self.assertFalse(proof['optimizer_used'])
            self.assertEqual(proof['input_backend'], 'zxux')
            self.assertNotEqual(result, assemble_candidate(asm),
                                'the echoed source must differ from raw proof')
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

    def test_rom_echo_and_delete_match_screen_at_same_frame(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        with tempfile.TemporaryDirectory(prefix='rbc-input-echo-') as tmp:
            bas, ssx = Path(tmp) / 'echo.bas', Path(tmp) / 'echo.ssx'
            bas.write_text('10 REM : OPEN #\n20 PRINT AT 0,0;"TYPE SOMETHING"\n'
                           '30 INPUT A$\n40 PRINT A$\n50 STOP\n', encoding='ascii')
            _, _, output, proof = compile_native(
                bas, CHECKPOINT, FRONTEND, TAPE, ROM, input_backend='zxux')
            self.assertTrue(proof['input_source_bridge_three_base_verified'])
            ssx.write_bytes(output)
            def screen(keys):
                run = rvm.run_kernel(ssx, keys=keys, frames=1000,
                                     system=SYSTEM)
                self.assertEqual(run.why, 'input', run.summary())
                return run.picture()[0]
            idle = screen('')
            entered = screen('{WAIT 200}ab')
            deleted = screen('{WAIT 200}abc{DELETE}')
            changed = screen('{WAIT 200}abc{DELETE}d')
            self.assertNotEqual(idle, entered, 'typed text was not echoed')
            self.assertEqual(entered, deleted, 'DELETE must clear the last cell')
            self.assertNotEqual(entered, changed,
                                'new character must appear after DELETE')


    def test_numeric_invalid_delete_and_reprompt(self):
        with tempfile.TemporaryDirectory(prefix='rbc-input-numeric-') as tmp:
            bas, ssx = Path(tmp) / 'numbers.bas', Path(tmp) / 'numbers.ssx'
            bas.write_text('10 REM : OPEN #\n20 INPUT A\n'
                           '30 IF A=1234 THEN POKE 22528,55\n40 STOP\n',
                           encoding='ascii')
            _, _, executable, proof = compile_native(
                bas, CHECKPOINT, FRONTEND, TAPE, ROM, input_backend='zxux')
            self.assertEqual(proof['input_backend'], 'zxux')
            ssx.write_bytes(executable)
            for keys in ('1234', '123x{DELETE}4',
                         'abc{ENTER}{WAIT 100}1234'):
                with self.subTest(keys=keys):
                    run = rvm.run_kernel(ssx,
                        keys='{WAIT 200}' + keys + '{ENTER}',
                        frames=2000, system=SYSTEM)
                    self.assertEqual(run.why, 'exit', run.summary())
                    self.assertEqual(run.fg.status, 0)
                    self.assertEqual(run.fg.exit_picture[0][6144], 55)
                    run.session.wait_prompt(1500)
                    self.assertEqual(run.session.last_line(), '#')

    def test_long_echo_input_never_overwrites_low_kernel(self):
        with tempfile.TemporaryDirectory(prefix='rbc-input-bounds-') as tmp:
            bas, ssx = Path(tmp) / 'bounds.bas', Path(tmp) / 'bounds.ssx'
            bas.write_text('10 REM : OPEN #\n20 INPUT A$\n'
                           '30 POKE 22528,LEN A$+20\n40 STOP\n',
                           encoding='ascii')
            _, _, executable, proof = compile_native(
                bas, CHECKPOINT, FRONTEND, TAPE, ROM, input_backend='zxux')
            ssx.write_bytes(executable)
            opts = rvm.Options()
            opts.prog = str(ssx)
            opts.system = SYSTEM
            opts.keys = '{WAIT 200}' + 'z'*120 + '{ENTER}'
            opts.frames = 2400
            run = rvm.Runner(opts)
            run.start()
            observed = []
            run.session.frame_hooks.append(lambda _: observed.append(
                run.session.word(0x5c65)) if run.fg.started is not None
                and run.fg.ended is None else None)
            for _ in range(5000):
                run.frame()
                why = run.check(2400)
                if why:
                    run.why = why
                    break
            self.assertEqual(run.why, 'exit', run.summary())
            self.assertEqual(run.fg.status, 0)
            self.assertTrue(observed)
            self.assertGreater(min(observed), 0x5d00)
            self.assertLess(max(observed), 0x5d98)
            run.session.wait_prompt(1500)
            self.assertEqual(run.session.last_line(), '#')

    def test_original_flying_geese_enter_starts_second_round(self):
        from test_native_oxo_complete_round import text_row
        game = ROOT / 'src/bonus/60-programs/39-flying-geese'
        bas = game / 'BASIC/39-flying-geese.bas'
        tzx = game / 'BASIC/39-flying-geese.tzx'
        published = game / 'bin/39-flying-geese.ssx'
        originals = tuple(p.read_bytes() for p in (bas, tzx, published))
        with tempfile.TemporaryDirectory(prefix='rbc-input-geese-') as tmp:
            _, _, trial, report = compile_native(
                bas, CHECKPOINT, FRONTEND, TAPE, ROM, input_backend='zxux')
            self.assertEqual(trial, originals[2])
            self.assertTrue(report['input_source_bridge_three_base_verified'])
            ssx = Path(tmp) / 'geese-input.ssx'
            ssx.write_bytes(trial)
            font = (CHECKPOINT / 'font32.bin').read_bytes()
            shots = '{WAIT 100}' + 'a'*130
            over = rvm.run_kernel(ssx, keys=shots,
                                  frames=4400, system=SYSTEM)
            self.assertEqual(over.why, 'input', over.summary())
            pic, _ = over.picture()
            self.assertEqual(text_row(pic, 9, font).strip(), 'GAME OVER')
            self.assertIn('IN 100 SHOTS', text_row(pic, 11, font))
            after = rvm.run_kernel(ssx, keys=shots+'{WAIT 150}{ENTER}',
                                   frames=5200, system=SYSTEM)
            self.assertEqual(after.why, 'frames', after.summary())
            final, _ = after.picture()
            self.assertNotEqual(pic, final)
            self.assertTrue(text_row(final, 0, font).strip().startswith('SHOTS:'))
            self.assertNotIn('GAME OVER', text_row(final, 9, font))
        self.assertEqual(tuple(p.read_bytes() for p in (bas, tzx, published)),
                         originals)


if __name__ == '__main__':
    unittest.main()

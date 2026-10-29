"""Real ZX-UX proof of default bounded INPUT, with ROM comparison retained.

Original BAS/TZX and the ZX-UX kernel remain unchanged. Published native
SSX must equal both independent, relocatable BAS/TZX compiler results.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'src/zx-ux-sdk'),
                str(ROOT/'experiments/hisoft-rbc-2026-10-22/stage'),
                str(ROOT/'experiments/hisoft-rbc-2026-10-22/tests')]
import rld
import rvm
from native_rbc_cli import compile_native
from native_input_six_pairs import GAMES, TEMP
from test_native_oxo_complete_round import text_row

CHECKPOINT = ROOT/'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT/'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT/'build/out/ZX-UX.tzx'
FROZEN = ROOT/'dist/zx-ux/tzx/ZX-UX.tzx'
ORIGINALS = ROOT/'src/bonus/60-programs'
READY = all(p.is_file() for p in (CHECKPOINT/'rbc.py', CHECKPOINT/'font32.bin',
            FRONTEND/'compiler.py', TAPE, ROM, SYSTEM, FROZEN))


@unittest.skipUnless(READY, 'verified HiSoft/Z80/ZX-UX inputs required')
class ProductionDefaultInput(unittest.TestCase):
    def test_default_uses_source_native_input_and_noninput_keeps_reference(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        with tempfile.TemporaryDirectory(prefix='rbc-input-default-') as tmp:
            source = Path(tmp)/'default.bas'
            source.write_text('10 REM : OPEN #\n20 INPUT A$\n30 STOP\n', encoding='ascii')
            _, _, native, proof = compile_native(source, CHECKPOINT, FRONTEND, TAPE, ROM)
            _, _, legacy, ref = compile_native(
                source, CHECKPOINT, FRONTEND, TAPE, ROM, input_backend='rom')
            self.assertEqual(proof['input_backend'], 'zxux')
            self.assertTrue(proof['input_source_bridge_three_base_verified'])
            self.assertTrue(proof['native_three_base_source_verified'])
            self.assertNotEqual(native, legacy)
            self.assertTrue(ref['native_and_legacy_ssx_byte_identical'])
            noinput = Path(tmp)/'noinput.bas'
            noinput.write_text('10 REM : OPEN #\n20 PRINT "HELLO"\n30 STOP\n',
                               encoding='ascii')
            _, _, a, pa = compile_native(noinput, CHECKPOINT, FRONTEND, TAPE, ROM)
            _, _, b, pb = compile_native(noinput, CHECKPOINT, FRONTEND, TAPE,
                                          ROM, input_backend='rom')
            self.assertEqual(a, b)
            self.assertEqual(pa['input_backend'], 'rom')
            self.assertEqual(pb['input_backend'], 'rom')

    def test_cursor_edit_delete_up_down_and_shell_restoration(self):
        with tempfile.TemporaryDirectory(prefix='rbc-input-controls-') as tmp:
            bas, ssx = Path(tmp)/'controls.bas', Path(tmp)/'controls.ssx'
            bas.write_text('10 REM : OPEN #\n20 INPUT A$\n'
                           '30 IF A$="abcd" THEN POKE 22528,55\n'
                           '40 STOP\n', encoding='ascii')
            _, _, blob, proof = compile_native(bas, CHECKPOINT, FRONTEND,
                                               TAPE, ROM)
            self.assertEqual(proof['input_backend'], 'zxux')
            self.assertLessEqual(max(proof['file'], proof['total']), 14000)
            ssx.write_bytes(blob)
            for keys in ('abcd', 'ac{LEFT}b{RIGHT}d',
                         'abcd{LEFT}{LEFT}{DELETE}b',
                         'ab{UP}cd', 'xyz{EDIT}abcd'):
                with self.subTest(keys=keys):
                    r = rvm.run_kernel(ssx, keys='{WAIT 200}'+keys+'{ENTER}',
                                       frames=1500, system=SYSTEM)
                    self.assertEqual((r.why, r.fg.status), ('exit', 0), r.summary())
                    self.assertEqual(r.fg.exit_picture[0][6144], 55)
                    self.assertFalse(r.session.owns_screen(r.fg.pid))
                    r.session.wait_prompt(1500)
                    self.assertEqual(r.session.last_line(), '#')
            down = rvm.run_kernel(ssx, keys='{WAIT 200}abc{DOWN}',
                                  frames=1500, system=SYSTEM)
            self.assertEqual((down.why, down.fg.status), ('exit', 1), down.summary())
            down.session.wait_prompt(1500)
            self.assertEqual(down.session.last_line(), '#')
            self.assertFalse(down.session.owns_screen(down.fg.pid))
            def image(keys):
                r = rvm.run_kernel(ssx, keys='{WAIT 200}'+keys, frames=900,
                                   system=SYSTEM)
                self.assertEqual(r.why, 'input', r.summary())
                return r.picture()[0]
            self.assertEqual(image('ab'), image('abc{DELETE}'))
            self.assertEqual(image('abcd'), image('ac{LEFT}b{RIGHT}d'))

    def test_all_six_independent_default_pairs_fit_native_loader(self):
        import hashlib
        for name in GAMES:
            with self.subTest(game=name):
                folder = TEMP/name
                variants = [(folder/f'from-{side}.ssx').read_bytes()
                            for side in ('bas', 'tzx')]
                self.assertEqual(variants[0], variants[1])
                published = ORIGINALS/name/'bin'/(name+'.ssx')
                self.assertEqual(published.read_bytes(), variants[0],
                                 'published INPUT game differs from independent sources')
                report = json.loads((folder/'bas-report.json').read_text())
                outcome = json.loads((folder/'bas-outcome.json').read_text())
                self.assertEqual(report['input_backend'], 'zxux')
                self.assertTrue(report['input_source_bridge_three_base_verified'])
                self.assertTrue(report['native_three_base_source_verified'])
                self.assertEqual(outcome['exit'], 0)
                self.assertEqual(outcome['sha256'], hashlib.sha256(variants[0]).hexdigest())
                image = rld.parse_ssx(variants[0])
                self.assertEqual(image['entry'], 0)
                self.assertTrue(image['relocs'])
                total = len(image['image']) + image['bss'] + image['stack']
                self.assertEqual(total, report['total'])
                self.assertLessEqual(max(total, len(variants[0])), 14000)

    def test_default_flying_geese_100_shots_enter_replay(self):
        path = ORIGINALS/'39-flying-geese'/'bin/39-flying-geese.ssx'
        self.assertTrue(path.is_file())
        font = (CHECKPOINT/'font32.bin').read_bytes()
        original = ORIGINALS/'39-flying-geese'/'bin/39-flying-geese.ssx'
        digest = hashlib.sha256(original.read_bytes()).hexdigest()
        shots = '{WAIT 100}' + 'a'*130
        over = rvm.run_kernel(path, keys=shots, frames=4400, system=SYSTEM)
        self.assertEqual(over.why, 'input', over.summary())
        picture, _ = over.picture()
        self.assertEqual(text_row(picture, 9, font).strip(), 'GAME OVER')
        self.assertIn('IN 100 SHOTS', text_row(picture, 11, font))
        replay = rvm.run_kernel(path, keys=shots+'{WAIT 150}{ENTER}',
                                frames=5200, system=SYSTEM)
        self.assertEqual(replay.why, 'frames', replay.summary())
        next_picture, _ = replay.picture()
        self.assertNotEqual(picture, next_picture)
        self.assertTrue(text_row(next_picture, 0, font).strip().startswith('SHOTS:'))
        self.assertNotIn('GAME OVER', text_row(next_picture, 9, font))
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()

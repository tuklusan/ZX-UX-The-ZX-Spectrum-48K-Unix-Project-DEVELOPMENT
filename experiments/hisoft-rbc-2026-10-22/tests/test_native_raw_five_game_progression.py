"""Five original INPUT games, bounded raw-source candidate only, real ZX-UX.

The actual game BAS, TZX, published SSX, ROM and kernel stay untouched.
Screen changes are input-flow checks, not complete gameplay or release approval.
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
from native_input_raw_candidate import assemble_candidate
from native_rbc_cli import compile_native
from test_native_input_original_games import run_screen, CASES
from test_native_oxo_complete_round import text_row
import rvm

CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
GAMES = ROOT / 'src/bonus/60-programs'
READY = all(p.is_file() for p in (
    CHECKPOINT / 'rbc.py', FRONTEND / 'compiler.py', TAPE, ROM,
    SYSTEM, FROZEN))


@unittest.skipUnless(READY, 'original compiler, ROM and ZX-UX required')
class OriginalFiveInputCandidates(unittest.TestCase):
    def setUp(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())

    def make(self, name, tmp):
        folder = GAMES / name
        inputs = (folder / 'BASIC' / (name+'.bas'),
                  folder / 'BASIC' / (name+'.tzx'),
                  folder / 'bin' / (name+'.ssx'))
        before = tuple(p.read_bytes() for p in inputs)
        asm, obj, old, proof = compile_native(
            inputs[0], CHECKPOINT, FRONTEND, TAPE, ROM)
        self.assertEqual(old, before[2])
        self.assertTrue(proof['native_three_base_source_verified'])
        self.assertTrue(proof['native_and_legacy_ssx_byte_identical'])
        self.assertFalse(proof['optimizer_used'])
        changed = assemble_candidate(asm)
        self.assertNotEqual(changed, old)
        trial = tmp / (name+'.ssx')
        trial.write_bytes(changed)
        return trial, inputs, before

    def test_biorhythms_and_roots_real_keyboard_response(self):
        with tempfile.TemporaryDirectory(prefix='raw-two-input-games-') as tmp:
            for name, keys, frames in CASES:
                with self.subTest(game=name):
                    trial, inputs, original = self.make(name, Path(tmp))
                    quiet, control_state = run_screen(trial, '', frames)
                    played, response_state = run_screen(trial, keys, frames)
                    self.assertEqual(control_state, 'input')
                    self.assertIn(response_state, ('input', 'frames'))
                    self.assertNotEqual(quiet, played)
                    self.assertEqual(tuple(p.read_bytes() for p in inputs),
                                     original)

    def test_critical_path_numeric_input_invalid_finish_is_rejected(self):
        name = '07-critical-path-analysis'
        with tempfile.TemporaryDirectory(prefix='raw-critical-path-') as tmp:
            trial, inputs, original = self.make(name, Path(tmp))
            intro = '{WAIT 200}{ENTER}{WAIT 200}{ENTER}{WAIT 200}{ENTER}'
            first = intro+'{WAIT 100}1{ENTER}'
            bad = first+'{WAIT 100}0{ENTER}'
            good = bad+'{WAIT 100}12{ENTER}'
            screens = [run_screen(trial, keys, 1900)
                       for keys in (intro, first, bad, good)]
            self.assertEqual([state for _, state in screens],
                             ['input', 'input', 'input', 'frames'])
            self.assertNotEqual(screens[0][0], screens[1][0])
            self.assertEqual(screens[1][0], screens[2][0])
            self.assertNotEqual(screens[2][0], screens[3][0])
            self.assertEqual(tuple(p.read_bytes() for p in inputs), original)


if __name__ == '__main__':
    unittest.main()

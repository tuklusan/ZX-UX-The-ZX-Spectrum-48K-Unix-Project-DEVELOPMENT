"""Real 48K kernel INPUT progression probes using original BAS game inputs.

The original compiled SSX files are never changed.  The experimental bridge
changes only independently witnessed pre-link source *inside this test*, then
runs genuine ras/rld and ZX-UX.  These screen changes are not complete gameplay
or production INPUT approval: user-entered numeric values and editor memory
bounds still require separate semantic and safety proof.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'experiments/hisoft-rbc-2026-10-22/tests'),
                str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import rvm
import rld
from native_rbc_cli import compile_native
from test_native_input_bridge_candidate import link_candidate

CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
GAMES = ROOT / 'src/bonus/60-programs'
READY = all(p.is_file() for p in (CHECKPOINT / 'rbc.py',
    CHECKPOINT / 'font32.bin', FRONTEND / 'compiler.py', TAPE, ROM,
    SYSTEM, FROZEN))

# Numbered source prompts, not invented keybindings: enter six dates in
# Biorhythms; advance successive Roots screens; keep each trial below a frame ceiling.
CASES = (
    ('23-biorhythms',
     '{WAIT 100}1980{ENTER}{WAIT 30}10{ENTER}{WAIT 30}28{ENTER}'
     '{WAIT 30}2026{ENTER}{WAIT 30}10{ENTER}{WAIT 30}28{ENTER}', 1500),
    ('56-roots', '{WAIT 300}{ENTER}{WAIT 200}{ENTER}{WAIT 200}{ENTER}', 1550),
)



def run_screen(program: Path, keys: str, frames: int) -> tuple[str, str]:
    result = rvm.run_kernel(program, keys=keys, frames=frames, system=SYSTEM)
    if result.fg.started is None or result.why not in ('frames', 'input', 'exit'):
        raise AssertionError('original ZX-UX did not run native process')
    if result.fg.ended is not None:
        if result.fg.status != 0 or result.session.owns_screen(result.fg.pid):
            raise AssertionError('native process did not exit cleanly')
        result.session.wait_prompt(1500)
        if result.session.last_line() != '#':
            raise AssertionError('ZX-UX shell prompt not restored')
    framebuffer, _ = result.picture()
    if len(framebuffer) != 6912:
        raise AssertionError('not a real 48K screen')
    return hashlib.sha256(framebuffer).hexdigest(), result.why


@unittest.skipUnless(READY, 'original HiSoft and real ZX-UX are required')
class NativeOriginalInputExperiments(unittest.TestCase):
    def test_two_original_game_listings_advance_with_source_bridge(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        for game, keys, frames in CASES:
            with self.subTest(game=game):
                original_bas = GAMES / game / 'BASIC' / (game + '.bas')
                published = GAMES / game / 'bin' / (game + '.ssx')
                before = original_bas.read_bytes()
                published_before = published.read_bytes()
                source, _, reference, proof = compile_native(
                    original_bas, CHECKPOINT, FRONTEND, TAPE, ROM, input_backend='rom')
                self.assertNotEqual(reference, published_before)
                self.assertEqual(compile_native(
                    original_bas, CHECKPOINT, FRONTEND, TAPE, ROM)[2],
                    published_before)
                self.assertTrue(proof['native_three_base_source_verified'])
                self.assertTrue(proof['native_and_legacy_ssx_byte_identical'])
                self.assertFalse(proof['optimizer_used'])
                native = link_candidate(source)
                self.assertNotEqual(native, reference)
                parsed = rld.parse_ssx(native)
                self.assertLessEqual(max(len(native), len(parsed['image']) +
                                         parsed['bss'] + parsed['stack']), 14000)
                import tempfile
                with tempfile.TemporaryDirectory(prefix='rbc-game-input-') as temp:
                    trial = Path(temp) / (game + '.ssx')
                    trial.write_bytes(native)
                    quiet, state_quiet = run_screen(trial, '', frames)
                    typed, state_typed = run_screen(trial, keys, frames)
                    self.assertNotEqual(quiet, typed,
                                        'native source experiment did not advance screen')
                    self.assertIn(state_quiet, ('frames', 'input', 'exit'))
                    self.assertIn(state_typed, ('frames', 'input', 'exit'))
                self.assertEqual(original_bas.read_bytes(), before)
                self.assertEqual(published.read_bytes(), published_before)


    def test_original_critical_path_all_three_input_stages_and_reprompt(self):
        # Original lines 570, 840, 890 await ENTER; 130/140 take numeric
        # start/finish nodes, and line 142 rejects finish node zero.
        game = '07-critical-path-analysis'
        basic = GAMES / game / 'BASIC' / (game + '.bas')
        published = GAMES / game / 'bin' / (game + '.ssx')
        original_bytes = basic.read_bytes()
        published_bytes = published.read_bytes()
        source, _, reference, proof = compile_native(
            basic, CHECKPOINT, FRONTEND, TAPE, ROM, input_backend='rom')
        self.assertNotEqual(reference, published_bytes)
        self.assertEqual(compile_native(
            basic, CHECKPOINT, FRONTEND, TAPE, ROM)[2], published_bytes)
        self.assertTrue(proof['native_three_base_source_verified'])
        self.assertTrue(proof['native_and_legacy_ssx_byte_identical'])
        self.assertFalse(proof['optimizer_used'])
        native = link_candidate(source)
        self.assertNotEqual(native, reference)
        linked = rld.parse_ssx(native)
        self.assertLessEqual(max(len(native), len(linked['image']) +
                                 linked['bss'] + linked['stack']), 14000)
        import tempfile
        with tempfile.TemporaryDirectory(prefix='rbc-path-input-') as temp:
            trial = Path(temp) / (game + '.ssx')
            trial.write_bytes(native)
            intro = '{WAIT 200}{ENTER}{WAIT 200}{ENTER}{WAIT 200}{ENTER}'
            first = intro + '{WAIT 100}1{ENTER}'
            bad_finish = first + '{WAIT 100}0{ENTER}'
            completed = bad_finish + '{WAIT 100}12{ENTER}'
            a, state_a = run_screen(trial, intro, 1900)
            b, state_b = run_screen(trial, first, 1900)
            c, state_c = run_screen(trial, bad_finish, 1900)
            d, state_d = run_screen(trial, completed, 1900)
            self.assertEqual((state_a, state_b, state_c, state_d),
                             ('input', 'input', 'input', 'frames'))
            self.assertNotEqual(a, b, 'first numeric INPUT did not advance')
            self.assertEqual(b, c, 'bad finish node was not rejected')
            self.assertNotEqual(c, d, 'valid finish node did not advance')
        self.assertEqual(basic.read_bytes(), original_bytes)
        self.assertEqual(published.read_bytes(), published_bytes)


if __name__ == '__main__':
    unittest.main()

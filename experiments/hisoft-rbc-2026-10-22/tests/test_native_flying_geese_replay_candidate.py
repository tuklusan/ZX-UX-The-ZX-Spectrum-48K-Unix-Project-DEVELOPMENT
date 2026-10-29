"""Witness genuine replay of original Flying Geese with a *test-only* INPUT bridge.

The published native SSX still uses the HiSoft ROM EDITOR and is NOT repaired
here. The bridge changes the independently checked pre-link assembly only;
no original BASIC, ROM, kernel, published executable, or linked image is edited.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'),
                str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'),
                str(Path(__file__).resolve().parent)]
import rld
import rvm
from native_rbc_cli import compile_native
from test_native_input_bridge_candidate import link_candidate
from test_native_oxo_complete_round import text_row

GAME = ROOT / 'src/bonus/60-programs/39-flying-geese'
BAS = GAME / 'BASIC/39-flying-geese.bas'
TZX = GAME / 'BASIC/39-flying-geese.tzx'
SSX = GAME / 'bin/39-flying-geese.ssx'
CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, ROM, SYSTEM, FROZEN,
    CHECKPOINT / 'rbc.py', CHECKPOINT / 'font32.bin',
    FRONTEND / 'compiler.py', TAPE))
SHOTS = '{WAIT 100}' + 'a'*130
REPLAY = SHOTS + '{WAIT 150}{ENTER}'


def row(screen, y, font):
    return text_row(screen, y, font).strip()


@unittest.skipUnless(READY, 'verified RBC frontend, tape, ZX-UX kernel required')
class NativeFlyingGeeseInputReplay(unittest.TestCase):
    def test_original_game_over_and_experimental_enter_replay(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
        font = (CHECKPOINT / 'font32.bin').read_bytes()
        self.assertEqual(len(font), 768)
        asm, obj, linked, proof = compile_native(
            BAS, CHECKPOINT, FRONTEND, TAPE, ROM, input_backend='rom')
        self.assertTrue(obj.startswith(b'SSO1'))
        self.assertNotEqual(linked, originals[2])
        self.assertEqual(compile_native(
            BAS, CHECKPOINT, FRONTEND, TAPE, ROM)[2], originals[2])
        self.assertTrue(proof['native_three_base_source_verified'])
        self.assertTrue(proof['native_and_legacy_ssx_byte_identical'])
        self.assertFalse(proof['optimizer_used'])
        experimental = link_candidate(asm)
        self.assertNotEqual(experimental, originals[2])
        image = rld.parse_ssx(experimental)
        self.assertEqual(image['entry'], 0)
        self.assertLessEqual(max(len(experimental), len(image['image']) +
                                 image['bss'] + image['stack']), 14000)
        with tempfile.TemporaryDirectory(prefix='rbc-geese-input-test-') as tmp:
            candidate = Path(tmp) / 'flying-geese-input-experimental.ssx'
            candidate.write_bytes(experimental)
            over = rvm.run_kernel(candidate, keys=SHOTS, frames=4400,
                                  system=SYSTEM)
            self.assertIsNotNone(over.fg.started)
            self.assertIsNone(over.fg.ended)
            self.assertTrue(over.session.owns_screen(over.fg.pid))
            old_screen, old_border = over.picture()
            self.assertEqual(over.why, 'input')
            self.assertEqual(row(old_screen, 9, font), 'GAME OVER')
            self.assertIn('IN 100 SHOTS', row(old_screen, 11, font))
            self.assertIn('HIGHEST SCORE', row(old_screen, 13, font))

            replay = rvm.run_kernel(candidate, keys=REPLAY, frames=5200,
                                    system=SYSTEM)
            self.assertIsNotNone(replay.fg.started)
            self.assertIsNone(replay.fg.ended)
            self.assertTrue(replay.session.owns_screen(replay.fg.pid))
            new_screen, new_border = replay.picture()
            self.assertEqual(replay.why, 'frames')
            self.assertNotEqual(hashlib.sha256(old_screen).digest(),
                                hashlib.sha256(new_screen).digest())
            self.assertTrue(row(new_screen, 0, font).startswith('SHOTS:'))
            self.assertNotIn('GAME OVER', row(new_screen, 9, font))
            self.assertNotIn('IN 100 SHOTS', row(new_screen, 11, font))
            if os.environ.get('RBC_GEESE_REPLAY_CAPTURE_DIR'):
                path = Path(os.environ['RBC_GEESE_REPLAY_CAPTURE_DIR'])
                path.mkdir(parents=True, exist_ok=True)
                rvm.write_png(old_screen, str(path / 'flying-geese-gameover-candidate.png'), old_border)
                rvm.write_png(new_screen, str(path / 'flying-geese-enter-replay-candidate.png'), new_border)

        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)),
                         originals, 'original game files changed')


if __name__ == '__main__':
    unittest.main()

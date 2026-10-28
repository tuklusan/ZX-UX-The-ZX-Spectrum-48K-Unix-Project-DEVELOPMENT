"""Script actual Bricklayer keys in the unmodified ZX-UX 48K emulator.

This is a bounded interaction probe, not a claim that every level has been
played to completion. No simulated input handler or fabricated framebuffer.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import rvm

GAME = '42-bricklayer'
BAS = ROOT / f'src/bonus/60-programs/{GAME}/BASIC/{GAME}.bas'
SSX = ROOT / f'src/bonus/60-programs/{GAME}/bin/{GAME}.ssx'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, SSX, SYSTEM, FROZEN))


@unittest.skipUnless(READY, 'original Bricklayer, published SSX and rebuilt system required')
class NativeBricklayerGameplay(unittest.TestCase):
    def test_real_keyboard_changes_bricklayer_gameplay(self):
        sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        self.assertEqual(sha(SYSTEM), sha(FROZEN))
        self.assertEqual(sha(BAS),
            '79d2236096c2460d7060db26a61792f998e0231b5675da415dd4088dea7e9e99')
        self.assertEqual(sha(SSX),
            '2da076ca4c4d209c66745fd0cbac4164c35598de23cafa06eeca8e6579528170')
        scenes = {}
        for key, script in (
            ('none', 'a{WAIT 120}z'),
            ('other', 'a{WAIT 120}z{WAIT 200}x'),
            ('bomb', 'a{WAIT 120}z{WAIT 200}z'),
            ('humanoid', 'a{WAIT 120}z{WAIT 200}m'),
        ):
            with self.subTest(key=key):
                result = rvm.run_kernel(SSX, keys=script, frames=750,
                                        system=SYSTEM, cache=True)
                self.assertEqual(result.why, 'frames', result.summary())
                self.assertIsNotNone(result.fg.started)
                self.assertTrue(result.fg.owned)
                image, _ = result.picture()
                self.assertEqual(len(image), 6912)
                scenes[key] = hashlib.sha256(image).hexdigest()
        self.assertEqual(scenes['none'], scenes['other'],
                         'irrelevant input must not change this deterministic scene')
        self.assertNotEqual(scenes['none'], scenes['bomb'],
                            'Z bomb input must affect actual native game display')
        self.assertNotEqual(scenes['none'], scenes['humanoid'],
                            'M humanoid input must affect actual native game display')
        self.assertNotEqual(scenes['bomb'], scenes['humanoid'],
                            'two game controls must not have identical effects')


if __name__ == '__main__':
    unittest.main()

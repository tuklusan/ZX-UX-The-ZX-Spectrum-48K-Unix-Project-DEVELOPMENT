"""Original Moonlander: reach a real crash, then start another flight.

Use the unchanged published SSX, original BASIC, frozen ZX-UX system tape
and real Z80 keyboard/framebuffer. This proves a losing round and replay,
not a successful landing or every control route.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'), str(Path(__file__).resolve().parent)]
import rld
import rvm
from test_native_oxo_complete_round import text_row

GAME = ROOT / 'src/bonus/60-programs/50-moonlander'
BAS = GAME / 'BASIC/50-moonlander.bas'
TZX = GAME / 'BASIC/50-moonlander.tzx'
SSX = GAME / 'bin/50-moonlander.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN,
                                  SYSTEM.with_name('kernel.json')))


@unittest.skipUnless(READY, 'original Moonlander, recovered font and ZX-UX required')
class NativeMoonlanderCrashReplay(unittest.TestCase):
    def test_engine_off_crash_and_new_flight(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
        linked = rld.parse_ssx(originals[2])
        self.assertEqual(linked['entry'], 0)
        self.assertLessEqual(max(len(originals[2]), len(linked['image']) +
                                 linked['bss'] + linked['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)

        run = rvm.run_kernel(SSX, keys='', frames=450, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        intro, _ = run.picture()
        self.assertEqual(text_row(intro, 2, font).strip(), 'MOON LANDER')
        self.assertEqual(text_row(intro, 21, font).strip(),
                         'Press any key to start')

        run.session.kb.type('a')
        for _ in range(250):
            run.frame()
        flight, _ = run.picture()
        self.assertIn('Height ', text_row(flight, 0, font))
        self.assertIn('Fuel ', text_row(flight, 2, font))
        self.assertNotIn('YOU HAVE CRASHED', text_row(flight, 11, font))

        run.session.kb.type('o')  # Original line 220 switches the engine off.
        for _ in range(600):
            run.frame()
        crashed, crash_border = run.picture()
        self.assertIn('YOU HAVE CRASHED', text_row(crashed, 11, font))
        self.assertIn('PRESS ANY KEY TO RESTART', text_row(crashed, 15, font))
        self.assertNotEqual(hashlib.sha256(flight).digest(),
                            hashlib.sha256(crashed).digest())
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))

        run.session.kb.type('a')
        for _ in range(350):
            run.frame()
        restarted, replay_border = run.picture()
        self.assertIn('Height ', text_row(restarted, 0, font))
        self.assertIn('Fuel ', text_row(restarted, 2, font))
        self.assertNotIn('YOU HAVE CRASHED', text_row(restarted, 11, font))
        self.assertNotIn('PRESS ANY KEY TO RESTART', text_row(restarted, 15, font))
        self.assertNotEqual(hashlib.sha256(crashed).digest(),
                            hashlib.sha256(restarted).digest())
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))

        if os.environ.get('RBC_MOONLANDER_CAPTURE_DIR'):
            out = Path(os.environ['RBC_MOONLANDER_CAPTURE_DIR'])
            out.mkdir(parents=True, exist_ok=True)
            rvm.write_png(crashed, str(out / 'moonlander-crashed.png'), crash_border)
            rvm.write_png(restarted, str(out / 'moonlander-restarted.png'), replay_border)
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)), originals)


if __name__ == '__main__':
    unittest.main()

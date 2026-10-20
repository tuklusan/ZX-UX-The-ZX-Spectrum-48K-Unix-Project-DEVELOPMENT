#!/usr/bin/env python3
"""Run bonus C48 pilots using the actual ZX-UX kernel in RVM."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'release/dist/sdk/bin/py')]
import rvm
import rtap
import zxscreen

BASE = ROOT / 'release/dist/bonus/60-programs'


class PilotRunTests(unittest.TestCase):
    def run_case(self, folder, name, keys, expected):
        base = BASE / folder
        ssx = base / 'C48/bin/ssx' / (name + '.ssx')
        tape = base / 'C48/bin/tzx' / (name + '.tzx')
        self.assertTrue(ssx.is_file())
        self.assertTrue(tape.is_file())
        blocks = rtap.tzx_blocks(tape.read_bytes())[1]
        self.assertEqual([record[1] for record in blocks], rtap.records(ssx.read_bytes(), name))
        self.assertTrue(list((base / 'BASIC/SCREENSHOTS').glob('*.png')))
        opts = rvm.Options()
        opts.prog = str(ssx)
        opts.headless = True
        opts.keys = keys
        runner = rvm.Runner(opts)
        runner.start()
        why = None
        for _ in range(4000):
            runner.frame()
            why = runner.check(limit=1600)
            if why:
                break
        self.assertIsNotNone(runner.fg.started, 'ZX-UX never launched program')
        self.assertIn(why, ('input', 'frames'))
        screen, _ = runner.picture()
        result = zxscreen.screen_text(screen)
        for word in expected:
            self.assertIn(word, result)
        return result

    def test_anagram_ordered_output(self):
        screen = self.run_case('51-anagrammatic', 'anagram',
                               '{WAIT 80}{SPACE}AE\\nN2\\n',
                               ('POSSIBLE ARRANGEMENTS', 'AE', 'EA', 'FINISHED'))
        self.assertIn('PRESS ANY KEY', screen)

    def test_roulette_survival(self):
        self.run_case('53-russian-roulette', 'roulette',
                      '{WAIT 80}aaab', ('RUSSIAN ROULETTE',
                                      'YOU SURVIVED', 'THIS SCORE: 100'))

    def test_roulette_live_chamber(self):
        self.run_case('53-russian-roulette', 'roulette',
                      '{WAIT 80}b', ('YOU', 'DEAD', 'BULLET IN 1'))


if __name__ == '__main__':
    unittest.main()

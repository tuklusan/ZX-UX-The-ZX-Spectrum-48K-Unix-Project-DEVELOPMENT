"""Prevent accepted BASIC cassette labels from being reused."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'build/tools/compile-rbc-collections.py'
spec = importlib.util.spec_from_file_location('compile_rbc_collections', SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CassetteLabels(unittest.TestCase):
    def test_existing_label_wins_collision(self):
        used = {'www.thespectrumshow.net': set(), 'numerical-analysis': set()}
        reserve = module.reserve_cassette_label
        self.assertTrue(reserve(used, 'www.thespectrumshow.net',
                                Path('22-xmas2022--SleighRide')))
        self.assertFalse(reserve(used, 'www.thespectrumshow.net',
                                 Path('22-xmas2022--XmasHolly')))
        self.assertEqual(used['www.thespectrumshow.net'], {'22XMAS2022'})
        self.assertTrue(reserve(used, 'numerical-analysis', Path('01-bisect')))
        self.assertTrue(reserve(used, 'www.thespectrumshow.net', Path('23-different')))
        self.assertFalse(reserve(used, 'www.thespectrumshow.net', Path('23-different')))


if __name__ == '__main__':
    unittest.main()

"""Fail-closed classification of bounded real-ZX-UX batch gameplay runs."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from native_gameplay_batch import classify


class NativeGameplayBatchClassification(unittest.TestCase):
    def test_changed_and_unverified_are_distinct(self):
        good = ('42-bricklayer: DISPLAY CHANGED [frames/frames]\n'
                'LIVE ZX-UX: 1 loaded; 1 display changes; '
                '0 input effects not proven\n')
        still = ('42-bricklayer: INPUT EFFECT UNVERIFIED [frames/input]\n'
                 'LIVE ZX-UX: 1 loaded; 0 display changes; '
                 '1 input effects not proven\n')
        self.assertTrue(classify('42-bricklayer', 0, good, '').startswith('DISPLAY'))
        self.assertTrue(classify('42-bricklayer', 1, still, '').startswith('SCREEN'))
        for code, out in ((1, good), (0, still), (0, ''),
                          (0, good + good), (0, good.replace('42-', '43-'))):
            with self.subTest(code=code, out=out[:20]):
                self.assertTrue(classify('42-bricklayer', code, out, '').startswith('ERROR'))


if __name__ == '__main__':
    unittest.main()

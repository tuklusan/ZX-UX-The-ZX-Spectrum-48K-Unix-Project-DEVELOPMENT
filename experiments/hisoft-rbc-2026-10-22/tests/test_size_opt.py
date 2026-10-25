"""Focused general string-bound analyses, without corpus-name exceptions."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from size_opt import prove_literal_string_bounds


class Keywords:
    CODE_FOR = {'LET': 241, 'REM': 234, 'INPUT': 238, 'READ': 227, 'DIM': 233}


def fit(rows):
    return prove_literal_string_bounds(b'', Keywords(), lambda _: rows)[0]


class FitCases(unittest.TestCase):
    def test_multiple_literals(self):
        self.assertEqual(fit([(10, b'\xf1 A$="YES":\xf1 A$="NO"\r')]),
                         ['LEN A$<=3'])

    def test_unbounded_input(self):
        self.assertEqual(fit([(10, b'\xf1 A$="YES"\r'),
                              (20, b'\xee "NAME";A$\r')]), [])

    def test_dynamic_value(self):
        self.assertEqual(fit([(10, b'\xf1 A$="YES"\r'),
                              (20, b'\xf1 A$=B$\r')]), [])

    def test_substrings(self):
        self.assertEqual(fit([(10, b'\xf1 A$="YES"\r'),
                              (20, b'\xf1 A$(1)="X"\r')]), [])

    def test_other_assignment_not_overlooked(self):
        self.assertEqual(fit([(10, b'\xf1 A$="YES"\r'),
                              (20, b'\xfd 1 \xcb \xf1 A$="TOOLONG"\r')]), [])

    def test_rem_does_not_count(self):
        self.assertEqual(fit([(10, b'\xf1 A$="YES":\xea \xf1 A$="LONG"\r')]),
                         ['LEN A$<=3'])

    def test_requires_two_preceding_lines(self):
        self.assertEqual(fit([(1, b'\xf1 A$="YES"\r')]), [])

    def test_control_codes_count_as_bytes(self):
        self.assertEqual(fit([(10, b'\xf1 A$="\x10\x01"\r')]),
                         ['LEN A$<=2'])


if __name__ == '__main__':
    unittest.main()

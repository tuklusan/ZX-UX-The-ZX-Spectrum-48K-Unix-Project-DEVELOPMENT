"""Preserve original Sinclair BASIC string operators and source literals."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from basic_listing import normalize_listing

class FallKeywordTests(unittest.TestCase):
    def test_original_fall_guy_result_expression(self):
        original = 'CLS :LET w$=(b$AND f=21)+(c$AND f1=21):IF f=21AND f1=21THEN GO TO 5050'
        expected = 'CLS :LET w$=(b$ AND  f=21)+(c$ AND  f1=21):IF f=21 AND  f1=21 THEN  GO TO 5050'
        self.assertEqual(normalize_listing(original), expected)
        self.assertEqual(original.count('$AND'), 2)

    def test_operators_after_numbers_and_strings(self):
        self.assertEqual(normalize_listing('IF x=21AND y=3OR z=4THEN RETURN'),
                         'IF x=21 AND  y=3 OR  z=4 THEN  RETURN')
        self.assertEqual(normalize_listing('LET a$=b$OR n=1'), 'LET a$=b$ OR  n=1')

    def test_ordinary_variable_names_remain_unsplit(self):
        for text in ('LET COMMAND=1', 'LET BAND=3', 'LET RAND=4',
                     'PRINT "b$AND x=1"', 'REM b$AND x=1'):
            with self.subTest(text=text):
                self.assertEqual(normalize_listing(text), text)

    def test_source_is_not_modified(self):
        text='LET w$=(b$AND f=21)+(c$AND f1=21)'
        self.assertIn('b$ AND ', normalize_listing(text))
        self.assertIn('b$AND ', text)
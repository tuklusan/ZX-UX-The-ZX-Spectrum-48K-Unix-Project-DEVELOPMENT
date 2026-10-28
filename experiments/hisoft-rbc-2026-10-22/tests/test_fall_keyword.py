"""Check original joined BASIC words through the sole strict input adapter."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from basic_listing import encode_strict_listing
from bas2tap import encode_program


class OriginalText(unittest.TestCase):
    def assert_original_tape_encoding(self, body):
        listing = '10 ' + body
        self.assertEqual(encode_strict_listing(listing),
                         encode_program(listing, syntax_check=False))

    def test_fall_guy_joined_operators_not_repaired(self):
        self.assert_original_tape_encoding(
            'CLS :LET w$=(b$AND f=21)+(c$AND f1=21):'
            'IF f=21AND f1=21THEN GO TO 5050')

    def test_unspaced_for_kept_as_original_tape_tokens(self):
        self.assert_original_tape_encoding('FOR J=11TO 1STEP -1')

    def test_missing_numeric_to_boundary_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing whitespace before TO'):
            encode_strict_listing('10 FOR I=1TO10')
        self.assert_original_tape_encoding('FOR I=1 TO 10')

    def test_strings_comments_and_identifiers_not_split(self):
        for body in ('LET COMMAND=1', 'LET BAND=3',
                     'PRINT "b$AND x=1"', 'REM b$AND x=1'):
            with self.subTest(body=body):
                self.assert_original_tape_encoding(body)


if __name__ == '__main__':
    unittest.main()

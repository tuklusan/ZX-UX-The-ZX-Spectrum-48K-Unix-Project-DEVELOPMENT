"""Verify the only external BASIC lexer is vendored BAS2TAP."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from basic_listing import encode_strict_listing


class StrictKeywords(unittest.TestCase):
    def body(self, source):
        record = encode_strict_listing('10 ' + source)
        length = int.from_bytes(record[2:4], 'little')
        return record[4:4 + length]

    def test_reserved_keyword_not_reinterpreted(self):
        self.assertIn(bytes((0xac,)), self.body('LET AT=123'))

    def test_print_position_keyword(self):
        self.assertIn(bytes((0xac,)), self.body('PRINT AT 2,0;"HI"'))

    def test_identifier_does_not_split_keywords(self):
        self.assertIn(b'MAT', self.body('LET MAT=5'))

    def test_literal_text_kept_unchanged(self):
        self.assertIn(b'"AT THEN PRINT"', self.body('PRINT "AT THEN PRINT"'))
        self.assertIn(b'AT THEN PRINT', self.body('REM AT THEN PRINT'))

    def test_unexpected_keyword_is_not_repaired(self):
        with self.assertRaises(ValueError):
            self.body('LET A=PRINT 1')


if __name__ == '__main__':
    unittest.main()
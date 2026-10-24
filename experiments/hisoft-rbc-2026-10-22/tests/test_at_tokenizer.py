"""A keyword used as a variable is not quietly rewritten to BASIC text."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from basic_listing import tokenize_preserving_numeric_at

class OriginalTokenizer:
    @staticmethod
    def tokenize_line(body, kw):
        return body.replace('AT', chr(0xac)).encode('latin-1')

class StrictKeywords(unittest.TestCase):
    def test_reserved_keyword_not_reinterpreted(self):
        self.assertIn(bytes([0xac]), tokenize_preserving_numeric_at(
            'LET AT=123', OriginalTokenizer(), None))

    def test_print_position_keyword(self):
        self.assertIn(bytes([0xac]), tokenize_preserving_numeric_at(
            'PRINT AT 2,0;"HI"', OriginalTokenizer(), None))

    def test_joined_tokens_not_repaired(self):
        line='IF DPOR LEN A$>2THEN LET FL=1'
        self.assertEqual(tokenize_preserving_numeric_at(line, OriginalTokenizer(), None),
                         line.encode('ascii'))

if __name__ == '__main__':
    unittest.main()
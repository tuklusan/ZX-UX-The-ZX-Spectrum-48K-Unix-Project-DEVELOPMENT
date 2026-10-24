"""The two inputs must be independently parsed, with no keyword repair."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from basic_listing import split_numbered_line, tokenize_preserving_numeric_at
from dual_source import SemanticDifference, semantic_check


def packing(data):
    return b'\x00\x0a' + len(data).to_bytes(2, 'little') + data


class Round2Fidelity(unittest.TestCase):
    def test_numbered_ascii_only(self):
        self.assertEqual(split_numbered_line('10 PRINT "HELLO"')[0], 10)
        with self.assertRaises(ValueError):
            split_numbered_line('PRINT "HELLO"')

    def test_no_non_ascii_guessing(self):
        with self.assertRaisesRegex(ValueError, 'non-ASCII'):
            tokenize_preserving_numeric_at('PRINT "\u00a3"', None, None)

    def test_missing_keyword_boundary_is_different(self):
        token_names = {0xEB: 'FOR', 0xCC: 'TO'}
        with self.assertRaisesRegex(SemanticDifference, 'Line 10'):
            semantic_check(packing(b'\xebI=1TO10\r'), packing(b'\xebI=1\xcc10\r'),
                           None, token_names, 'BAS/TZX')

    def test_string_and_comment_bytes_never_ignored(self):
        with self.assertRaisesRegex(SemanticDifference, 'Line 10'):
            semantic_check(packing(b'\xea  A  B\r'), packing(b'\xea A B\r'),
                           None, {0xEA: 'REM'}, 'BAS/TZX')

    def test_numeric_spelling_must_match_even_if_cache_differs(self):
        with self.assertRaisesRegex(SemanticDifference, 'Line 10'):
            semantic_check(packing(b'12\x0e\0\0\x0c\0\0\r'),
                           packing(b'13\x0e\0\0\x0c\0\0\r'), None, {}, 'BAS/TZX')


if __name__ == '__main__':
    unittest.main()

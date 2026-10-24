"""Both inputs are independently tokenized and compared without keyword repair."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from basic_listing import split_numbered_line, encode_strict_listing
from dual_source import SemanticDifference, semantic_check


def packing(data):
    return b'\x00\x0a' + len(data).to_bytes(2, 'little') + data


class Round2Fidelity(unittest.TestCase):
    def test_numbered_ascii_only(self):
        self.assertEqual(split_numbered_line('10 PRINT "HELLO"')[0], 10)
        with self.assertRaises(ValueError):
            encode_strict_listing('PRINT "HELLO"')

    def test_no_non_ascii_guessing(self):
        with self.assertRaisesRegex(ValueError, 'non-ASCII'):
            encode_strict_listing('10 PRINT "\u00a3"')

    def test_missing_keyword_boundary_is_different(self):
        token_names = {0xEB: 'FOR', 0xCC: 'TO'}
        with self.assertRaisesRegex(SemanticDifference, 'Line 10'):
            semantic_check(packing(b'\xebI=1TO10\r'), packing(b'\xebI=1\xcc10\r'),
                           None, token_names, 'BAS/TZX')

    def test_rem_contents_are_ignored_but_strings_are_not(self):
        semantic_check(packing(b'\xea  A  B\r'), packing(b'\xea A B\r'),
                       None, {0xEA: 'REM'}, 'BAS/TZX')
        with self.assertRaisesRegex(SemanticDifference, 'Line 10'):
            semantic_check(packing(b'\xf5\"A  B\"\r'), packing(b'\xf5\"A B\"\r'),
                           None, {0xF5: 'PRINT'}, 'BAS/TZX')

    def test_numeric_spelling_must_match_even_if_cache_differs(self):
        with self.assertRaisesRegex(SemanticDifference, 'Line 10'):
            semantic_check(packing(b'12\x0e\0\0\x0c\0\0\r'),
                           packing(b'13\x0e\0\0\x0c\0\0\r'), None, {}, 'BAS/TZX')
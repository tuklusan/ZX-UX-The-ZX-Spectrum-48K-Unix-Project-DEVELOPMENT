"""BAS/TZX fidelity: only ROM-irrelevant formatting may be ignored."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from dual_source import SemanticDifference, LosslessConversionError, validated_lines, semantic_check


def pack(rows):
    return b''.join(bytes((n >> 8, n & 255, len(b) & 255, len(b) >> 8)) + b
                    for n, b in rows)


T = {0xF5: 'PRINT', 0xCB: 'THEN', 0xFA: 'IF', 0xEB: 'FOR', 0xCC: 'TO'}


class Fidelity(unittest.TestCase):
    def compare(self, a, b):
        return semantic_check(pack([(10, a)]), pack([(10, b)]), validated_lines, T, 'BAS/TZX')

    def test_identical_and_keyword_only_spaces(self):
        self.compare(b'\xf5"abc"\r', b'\xf5 "abc"\r')

    def test_literal_spelling_is_not_repaired(self):
        with self.assertRaisesRegex(SemanticDifference, 'Line 10'):
            self.compare(b'\xebI=1TO10\r', b'\xebI=1\xcc10\r')

    def test_remark_and_string_bytes_are_exact(self):
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xf5"A B"\r', b'\xf5"AB"\r')
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xea A B\r', b'\xea A  B\r')

    def test_regenerated_numeric_cache_is_not_source(self):
        self.compare(b'\xf510\x0e\x00\x00\x0a\x00\x00\r',
                     b'\xf510\x0e\x00\x00\x0a\x00\x00\r')
        self.compare(b'\xf510\x0e\x00\x00\x0a\x00\x00\r',
                     b'\xf510\x0e\x01\x00\x00\x00\x00\r')
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xf510\r', b'\xf511\r')

    def test_rejects_bad_line_structure(self):
        with self.assertRaisesRegex(LosslessConversionError, 'non-increasing'):
            validated_lines(pack([(10, b'\xf5\r'), (10, b'\xf5\r')]))
        with self.assertRaisesRegex(LosslessConversionError, 'end-of-line'):
            validated_lines(pack([(10, b'\xf5')]))


if __name__ == '__main__':
    unittest.main()

"""Original Sinclair tape input must round-trip through ASCII without repair."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from tzx_ascii import LosslessConversionError, to_ascii_listing, confirm_roundtrip


TOKENS = {0xF5: 'PRINT', 0xEA: 'REM', 0xED: 'GO SUB', 0xCB: 'THEN', 0xFA: 'IF'}


class TapeAsciiTests(unittest.TestCase):
    def test_keywords_have_known_boundaries(self):
        result = to_ascii_listing([(10, b'\xfa 1\x0e\x00\x00\x01\x00\x00\xcb\xf5 "OK"\r')], TOKENS)
        self.assertIn(' IF ', result)
        self.assertIn(' THEN ', result)
        self.assertNotIn('0E', result)

    def test_printable_characters_and_spaces_survive(self):
        result = to_ascii_listing([(10, b'\xf5 "Hi {90} \xf5"\r')], TOKENS)
        self.assertIn('{20}', result)
        self.assertIn('{7B}90{7D}', result)
        self.assertIn('{F5}', result)

    def test_rem_does_not_create_keywords(self):
        result = to_ascii_listing([(10, b'\xea \xf5 SAVE\r')], TOKENS)
        self.assertIn('{F5}', result)
        self.assertIn('{20}SAVE', result)

    def test_identical_program_is_accepted(self):
        confirm_roundtrip(b'abc', b'abc', lambda _: [])

    def test_changed_hidden_numeric_bytes_fail(self):
        orig = b'abc'; modified = b'abd'
        with self.assertRaisesRegex(LosslessConversionError, 'Line 10: token round-trip'):
            confirm_roundtrip(orig, modified,
                              lambda x: [(10, b'1\x0e' + (b'12345' if x == orig else b'12346'))])

    def test_unknown_line_and_unsupported_cache(self):
        with self.assertRaisesRegex(LosslessConversionError, 'numeric cache'):
            to_ascii_listing([(10, b'\xf5 1\x0e\x01\r')], TOKENS)
        with self.assertRaisesRegex(LosslessConversionError, 'number'):
            to_ascii_listing([(10000, b'\xf5 1\r')], TOKENS)

if __name__ == '__main__':
    unittest.main()

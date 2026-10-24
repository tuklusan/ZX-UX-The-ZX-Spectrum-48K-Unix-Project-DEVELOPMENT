"""Standalone compiler rejects actual tape tokens, not quoted text."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from tape_policy import UnsupportedTapeOperation, reject_tape_operations


NAMES = {0xEF: 'LOAD', 0xF8: 'SAVE', 0xD5: 'MERGE', 0xD6: 'VERIFY'}


def check(*rows):
    return reject_tape_operations([(10 + i * 10, row) for i, row in enumerate(rows)], NAMES)


class TapeTests(unittest.TestCase):
    def test_bans_each_command(self):
        for code, name in NAMES.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(UnsupportedTapeOperation, 'Line 20: ' + name):
                    check(b'\xf5 "safe"', b'\xf5:' + bytes([code]) + b' "test"')

    def test_literal_strings_are_not_commands(self):
        check(b'\xf5 "' + bytes(NAMES) + b'"', b'\xf5 "LOAD SAVE MERGE VERIFY"')

    def test_rem_ignores_arbitrary_token_bytes(self):
        check(b'\xea ' + bytes(NAMES))
        check(b'\xf5 2:\xea ' + bytes(NAMES))

    def test_data_is_inert_until_colon(self):
        check(b'\xe4 ' + bytes(NAMES) + b',"x:y"')
        with self.assertRaisesRegex(UnsupportedTapeOperation, 'Line 10: LOAD'):
            check(b'\xe4 "x:y", ' + bytes([0xF8]) + b':' + bytes([0xEF]))

    def test_hidden_numeric_bytes_are_ignored(self):
        check(b'\xf5 1\x0e' + bytes([0xEF, 0xF8, 0xD5, 0xD6, 0x00]))

    def test_byte_text_is_not_keyword(self):
        check(b'\xf5 "LOAD":\xf5 3')

    def test_missing_keyword_table_fails_closed(self):
        with self.assertRaisesRegex(UnsupportedTapeOperation, 'missing original'):
            reject_tape_operations([(10, b'')], {})

if __name__ == '__main__':
    unittest.main()

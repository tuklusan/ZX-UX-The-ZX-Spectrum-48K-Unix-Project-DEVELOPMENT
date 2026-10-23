"""Check SSX1 variable addresses against native font and process storage."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from bss_layout import target_offset


class NativeVariableRelocation(unittest.TestCase):
    def test_invaders_variable_pointer_skips_768_byte_font(self):
        # This exact native variable write overlapped font byte 136 before fix.
        code_base, code_len, img_len = 54486, 8436, 9440
        original = 63062
        old_wrong_address = 64 + (original - code_base)
        self.assertEqual(old_wrong_address, 8640)
        self.assertEqual(old_wrong_address - (64 + code_len + 4), 136)
        self.assertEqual(target_offset(original, code_base, code_len,
                                       64, img_len, 2446), 9580)

    def test_galaxians_variable_zero(self):
        self.assertEqual(target_offset(57113 + 7132, 57113, 7132,
                                       64, 8136, 1123), 8136)

    def test_code_references_do_not_move(self):
        self.assertEqual(target_offset(54486 + 120, 54486, 8436,
                                       64, 9440, 2446), 184)
        self.assertEqual(target_offset(54486, 54486, 8436,
                                       64, 9440, 2446), 64)

    def test_last_variable_byte_and_end_boundary(self):
        self.assertEqual(target_offset(54486+8436+2445, 54486, 8436,
                                       64, 9440, 2446), 9440+2445)
        self.assertEqual(target_offset(54486+8436+2446, 54486, 8436,
                                       64, 9440, 2446), 9440+2446)

    def test_invalid_address_is_rejected(self):
        for address in (54485, 54486+8436+2447):
            with self.subTest(address=address), self.assertRaises(ValueError):
                target_offset(address, 54486, 8436, 64, 9440, 2446)


if __name__ == '__main__':
    unittest.main()

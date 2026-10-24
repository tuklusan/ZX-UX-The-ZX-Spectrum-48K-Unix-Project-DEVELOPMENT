"""Real Spectrum 48K ROM validation does not execute the BASIC source."""
import sys
import unittest
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'), str(Path(__file__).resolve().parents[1]/'stage')]
from rom_syntax import validate_rom_lines, RomSyntaxError

class OriginalRomSyntax(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (ROOT/'src/zx-ux-sdk/rom/48.rom').read_bytes()
        cls.old = sys.modules.get('tap')
        cls.tap = ModuleType('tap')
        sys.modules['tap'] = cls.tap

    @classmethod
    def tearDownClass(cls):
        if cls.old is None:
            del sys.modules['tap']
        else:
            sys.modules['tap'] = cls.old

    def check(self, body):
        self.tap.split_lines = lambda _: [(10, body + b'\r')]
        return validate_rom_lines(b'dummy',self.rom)

    def test_valid_print(self):
        self.assertEqual(self.check(b'\xf5 "HELLO"'),1)

    def test_valid_for(self):
        self.assertEqual(self.check(b'\xeb I=1 \xcc 10:\xf3 I'),1)

    def test_missing_to_token_is_invalid(self):
        with self.assertRaisesRegex(RomSyntaxError,'Line 10'):
            self.check(b'\xeb I=1TO10:\xf3 I')

    def test_original_numeric_caches_are_not_double_encoded(self):
        # Stored Sinclair BASIC has cached binary values after visible digits.
        self.assertEqual(self.check(b'\xed 9000\x0e\x00\x00\x28\x23\x00'), 1)
        self.assertEqual(self.check(b'\xeb I=1\x0e\x00\x00\x01\x00\x00 '
                                    b'\xcc 10\x0e\x00\x00\x0a\x00\x00:\xf3 I'), 1)

    def test_bad_stored_numeric_cache_is_rejected(self):
        with self.assertRaisesRegex(RomSyntaxError, 'numeric encoding'):
            self.check(b'\xf5 1\x0e\x00')

    def test_invalid_statement(self):
        with self.assertRaisesRegex(RomSyntaxError,'ROM syntax error'):
            self.check(b'\xf5 "HELLO"\xf4')

if __name__ == '__main__':unittest.main()

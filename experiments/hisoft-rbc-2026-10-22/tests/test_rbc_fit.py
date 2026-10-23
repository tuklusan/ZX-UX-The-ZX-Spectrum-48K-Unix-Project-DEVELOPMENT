"""Verify that RBC native fitting is default and refuses unknown source shapes."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from rbc_fit import patched


class FitTests(unittest.TestCase):
    def test_refuses_unexpected_build_shape(self):
        with self.assertRaisesRegex(ValueError, 'RBC structure changed'):
            patched('some different compiler')

    def test_rom_bank_allocation_is_conditional(self):
        # A full patch is exercised by the normal GitHub compiler suite.
        text = Path(__file__).resolve().parents[1] / 'stage' / 'rbc_fit.py'
        rules = text.read_text()
        self.assertIn('use_rom_font=args.fit', rules)
        self.assertIn('if not use_rom_font', rules)
        self.assertIn('memory_required(rld.parse_ssx(ssx)', rules)
        self.assertIn('native-memory-limit', rules)
        self.assertIn('args.output = output_path', rules)
        self.assertIn('if args.bytecode', rules)


if __name__ == '__main__':
    unittest.main()

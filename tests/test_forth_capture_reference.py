"""Forth native frame selection must distinguish output from loading screens."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/tools'))
from compiler_portfolio import CAPTURE, fuse_config
from fuse_portfolio import console_output_match


class ForthCaptureTests(unittest.TestCase):
    def test_native_console_rows_match_only_real_program_output(self):
        reference = Image.new('L', (256, 192))
        drawer = ImageDraw.Draw(reference)
        for y in (96, 104, 112, 120):
            drawer.rectangle((30, y, 150, y + 2), fill=255)
            drawer.rectangle((64, y + 4, 105, y + 5), fill=255)
        real = Image.new('L', (320, 240))
        # A genuine native screen can scroll by a whole console row.
        real.paste(reference, (32, 24 + 8))
        loader = Image.new('L', (320, 240))
        ImageDraw.Draw(loader).rectangle((30, 90, 100, 94), fill=255)
        self.assertGreaterEqual(console_output_match(reference, real), .95)
        self.assertLess(console_output_match(reference, loader), .65)

    def test_forth_uses_long_native_capture_and_independent_reference(self):
        with patch.dict(CAPTURE, {}, clear=True):
            config = fuse_config('rfc', 'sample', 'FTH99', Path('/sample.ssx'), 8)
        self.assertGreaterEqual(config['fuse_wait'], 90)
        self.assertGreaterEqual(config['type_key_pause'], .20)
        self.assertTrue(config['console_reference'])
        self.assertTrue(config['stop_on_reference_match'])
        self.assertEqual(config['reference'].name, 'sample.png')

    def test_existing_other_compiler_overrides_still_apply(self):
        with patch.dict(CAPTURE, {'rpc:sample': {'fuse_wait': 16,
                                                'sample_step': .09}}, clear=True):
            config = fuse_config('rpc', 'sample', 'PAS99', Path('/sample.ssx'), 8)
        self.assertEqual(config['fuse_wait'], 16)
        self.assertEqual(config['sample_step'], .09)
        self.assertFalse(config.get('console_reference', False))


if __name__ == '__main__':
    unittest.main()

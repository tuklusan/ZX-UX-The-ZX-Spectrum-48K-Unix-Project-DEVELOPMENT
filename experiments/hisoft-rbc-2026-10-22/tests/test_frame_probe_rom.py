"""ROM font frame verification is strict about both pointer and glyph data."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from frame_probe_rom import printable_rom_font, verify_rom_pointer


class RomFrameTests(unittest.TestCase):
    def test_rom_glyph_bounds(self):
        raw = bytes(range(256)) * 64
        self.assertEqual(printable_rom_font(raw), raw[0x3D00:0x4000])
        self.assertEqual(len(printable_rom_font(raw)), 768)
        with self.assertRaises(ValueError):
            printable_rom_font(bytes(8000))

    def test_live_rom_font_bytes_and_pointer_are_required(self):
        good = [{'label':'idle','chars_pointer':0x3C00,'font_state':{'font_intact':True}}]
        verify_rom_pointer(good)
        with self.assertRaisesRegex(AssertionError,'pointer'):
            verify_rom_pointer([{**good[0], 'chars_pointer':0xC000}])
        with self.assertRaisesRegex(AssertionError,'bytes'):
            verify_rom_pointer([{**good[0], 'font_state':{'font_intact':False}}])
        with self.assertRaisesRegex(AssertionError,'missing'):
            verify_rom_pointer([])


if __name__ == '__main__':
    unittest.main()

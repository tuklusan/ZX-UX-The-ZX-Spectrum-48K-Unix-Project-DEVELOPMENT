"""Font memory must never outlive an RBC process."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))


class Round2Fonts(unittest.TestCase):
    def state(self):
        from spectrum_fonts import ProcessFontState
        return ProcessFontState()

    def test_custom_glyph_storage_is_private(self):
        a, b = self.state(), self.state()
        a.poke_glyph(65, 0, 0xAA)
        self.assertNotEqual(b.peek_glyph(65, 0), 0xAA)

    def test_custom_charset_pointer_is_virtual(self):
        a = self.state()
        a.poke(23606, 0)
        a.poke(23607, 60)
        self.assertEqual(a.peek(23606), 0)
        self.assertEqual(a.peek(23607), 60)

    def test_ordinary_font_rewrite_outside_udg(self):
        a = self.state()
        a.poke_glyph(35, 7, 0x9C)
        self.assertEqual(a.peek_glyph(35, 7), 0x9C)

    def test_font_restoration_after_stop(self):
        a = self.state()
        original = a.shell_font_snapshot()
        a.poke_glyph(66, 2, 0xA5)
        a.exit('STOP')
        self.assertEqual(a.shell_font_snapshot(), original)

    def test_font_restoration_after_runtime_error(self):
        a = self.state()
        original = a.shell_font_snapshot()
        a.poke_glyph(68, 5, 0xE5)
        a.exit('runtime_error')
        self.assertEqual(a.shell_font_snapshot(), original)


if __name__ == '__main__':
    unittest.main()

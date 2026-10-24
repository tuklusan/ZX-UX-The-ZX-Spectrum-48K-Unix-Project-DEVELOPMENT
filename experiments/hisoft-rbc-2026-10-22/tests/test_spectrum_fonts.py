"""Exact token-source hints for private-font allocation, never rewrites."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from spectrum_fonts import ProcessFontState, detect_font_bank

class Fonts(unittest.TestCase):
    def _find(self,listing):
        lines=[]
        for row in listing.splitlines():
            no, body = row.split(' ', 1)
            tokenized=body.replace('POKE','\xf4').encode('latin-1')+b'\r'
            lines.append((int(no),tokenized))
        return detect_font_bank(lines,{0xf4:'POKE'})

    def test_scuba_style_bank_detected_without_changing_source(self):
        a=self._find('10 POKE 23606,0:POKE 23607,60\n20 POKE 60256,7\n30 POKE 23606,96:POKE 23607,235')
        self.assertEqual(a,(60256,True))

    def test_dynamic_font_pointer_never_assumed_constant(self):
        self.assertEqual(self._find('10 POKE 23606,A:POKE 23607,B'),(None,True))

    def test_original_rom_pointer_not_forced_to_private_bank(self):
        self.assertEqual(self._find('10 POKE 23606,0:POKE 23607,60'),(None,True))

    def test_multiple_font_banks_are_not_guessed(self):
        a=self._find('10 POKE 23606,96:POKE 23607,235\n20 POKE 23606,0:POKE 23607,240')
        self.assertEqual(a,(None,True))

    def test_private_font_cannot_leak_into_next_process(self):
        p=ProcessFontState(rom_font=bytes(768))
        p.poke_glyph(65,0,0x4f)
        p.exit('normal')
        q=ProcessFontState(rom_font=bytes(768))
        self.assertEqual(q.peek_glyph(65,0),0)
        with self.assertRaises(ValueError):p.peek_glyph(65,0)


if __name__=='__main__':unittest.main()

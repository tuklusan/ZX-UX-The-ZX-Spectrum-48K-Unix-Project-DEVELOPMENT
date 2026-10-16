"""New UI bootstrap invariants; dynamic 48K/FUSE remains a separate gate."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'release/build'))
from turbo_boot_build import encode_basic, progress_lines, expanded_line

class TurboPresentationTest(unittest.TestCase):
    def test_reference_messages_and_corrected_clock(self):
        p=ROOT/'release/src/zx-ux/turbo_lines.txt'
        rows=p.read_text().splitlines()
        self.assertEqual(len(rows),24)
        self.assertEqual(rows[0],'ZX-UX UNIX v1 / SPECTRUM 48K')
        self.assertEqual(rows[11],'console: 64 columns')
        self.assertEqual(rows[21],'default time: 09:00:00')
        self.assertTrue(all(len(x)<=32 for x in rows))
        self.assertEqual(tuple(x.ljust(32) for x in rows), progress_lines(25596, {},8171,11888))
    def test_font64_data_size_and_interleaved_layout(self):
        raw=(ROOT/'release/src/zx-ux/font4x8.bin').read_bytes()
        self.assertEqual(raw[:4],b'F4X8')
        self.assertEqual(len(raw[8:]),384)
        for line in progress_lines(25596,{},8171,11888):
            rendered=expanded_line(line)
            self.assertEqual(len(rendered),64)
            self.assertEqual(rendered[::2],line)
            self.assertEqual(rendered[1::2],' '*32)
    def test_basic_sets_half_height_rainbow_after_clear(self):
        data=encode_basic()
        self.assertIn(b'52991',data)
        self.assertIn(b'53248',data)
        self.assertLess(data.index(b'\xef""\xaf'),data.index(b'\xfb'))
        self.assertLess(data.index(b'\xfb'),data.index(b'23292'))
        for address,value in [(23292,16),(23293,48),(23294,32),(23295,40)]:
            self.assertIn(str(address).encode(),data)
            self.assertIn(b','+bytes([0xb0])+b'"'+str(value).encode()+b'"',data)
        self.assertIn(b'20732',data)
        self.assertIn(b'256',data)
        self.assertIn(b'255',data)
    def test_renderer_guards_last_four_8px_cells(self):
        source=(ROOT/'release/src/zx-ux/turbo_boot.asm').read_text()
        self.assertIn('ld c,28',source)
        self.assertIn('ld b,28',source)
        self.assertIn('incbin "font4x8.bin",8,384',source)
        self.assertNotIn('ld bc,017FFh',source)
        self.assertIn('out (0FEh),a             ; black border at ZX-UX handover',source)
if __name__=='__main__': unittest.main()

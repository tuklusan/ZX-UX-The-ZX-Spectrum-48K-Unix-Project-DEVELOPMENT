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
        self.assertLess(data.index(b'\xfb'),data.index(b'\xf5#'))
        # Use a VAL stream number because BASIC has no hidden number token.
        self.assertIn(b'\xf5#\xb0"1";\xac\xb0"1",\xb0"28";',data)
        self.assertEqual(data.count(b'"\x83"'),4)
        for paper in (2,6,4,5):
            self.assertIn(b'\xda\xb0"'+str(paper).encode()+b'";"\x83";',data)
        self.assertNotIn(b'23292',data)
        self.assertNotIn(b'20732',data)

    def test_final_line_precedes_final_block_without_early_exec(self):
        # User-visible row 24 is painted before the last tape packet starts,
        # but ordinal, CRC, length and XOR still gate the execution jump.
        src=(ROOT/'release/src/zx-ux/turbo_boot.asm').read_text()
        segment=src.split('.next:',1)[1].split('.receive:',1)[0]
        self.assertIn('cp 24',segment)
        self.assertIn('call render_text_row',segment)
        valid=src.split('.valid:',1)[1].split('; Read a transition',1)[0]
        self.assertIn('call copy_payload',valid)
        self.assertIn('cp 24',valid)
        self.assertIn('jr z,.already_drawn',valid)
        self.assertIn('jp 06000h',valid)
        self.assertLess(valid.index('call copy_payload'),valid.index('jp 06000h'))

    def test_tape_border_pattern_does_not_delay_bit_sampler(self):
        src=(ROOT/'release/src/zx-ux/turbo_boot.asm').read_text()
        edge=src.split('read_edge:',1)[1].split('find_pilot:',1)[0]
        pilot=src.split('find_pilot:',1)[1].split('read_byte:',1)[0]
        dat=src.split('receive_frame:',1)[1].split('validate_frame:',1)[0]
        self.assertNotIn('out (0FEh),a',edge,
                         'time-critical edge reader must not write border')
        self.assertIn('out (0FEh),a',pilot,
                      'pilot pulses should generate blue/black stripes')
        self.assertIn('ld a,l\n        and 1\n        out (0FEh),a',dat,
                      'data bytes should generate blue/black stripes')
        self.assertIn('out (0FEh),a             ; black border at ZX-UX handover',src)

    def test_renderer_guards_last_four_8px_cells(self):
        source=(ROOT/'release/src/zx-ux/turbo_boot.asm').read_text()
        self.assertIn('ld c,28',source)
        self.assertIn('ld b,28',source)
        self.assertIn('incbin "font4x8.bin",8,384',source)
        self.assertNotIn('ld bc,017FFh',source)
        self.assertIn('out (0FEh),a             ; black border at ZX-UX handover',source)
if __name__=='__main__': unittest.main()

"""Verify the actual native assembler/linker path for the ZX-UX wrapper."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import rld
from native_wrapper_source import NativeWrapperError, assemble_link, wrapper_source


SOURCE = '''    section text
    global start
start:
    ld hl,datum
    ret
    section data
datum:
    db 2,3,5
    section bss
    ds 8
'''


class NativeWrapperSource(unittest.TestCase):
    def test_assembler_linker_and_original_source_data(self):
        font = bytes(range(256)) * 3
        for rom in (True, False):
            with self.subTest(use_rom_font=rom):
                text, obj, ssx = assemble_link(SOURCE, font, use_rom_font=rom)
                info = rld.parse_ssx(ssx)
                self.assertTrue(obj.startswith(b'SSO1'))
                self.assertEqual(info['entry'], 0)
                self.assertEqual(info['bss'], 8)
                self.assertEqual(info['stack'], 384)
                self.assertIn('call rbc_wrapper_hisoft_entry', text)
                self.assertIn('dw rbc_wrapper_exit', text)
                self.assertIn('rbc_wrapper_hisoft_entry:', text)
                self.assertIn(b'\x02\x03\x05', info['image'])
                self.assertIn(b'\x00' * 168, info['image'])
                if rom:
                    self.assertNotIn(bytes(range(256)), info['image'])
                else:
                    self.assertIn(bytes(range(256)), info['image'])
                self.assertGreaterEqual(len(info['relocs']), 20)

    def test_restart_slot_is_symbolic_bss_reference(self):
        source, _, ssx = assemble_link(SOURCE, bytes(768), restart_slot=True)
        self.assertIn('ld (rbc_wrapper_bss_end-2),sp', source)
        self.assertIn('jp rbc_wrapper_hisoft_entry', source)
        self.assertEqual(rld.parse_ssx(ssx)['bss'], 8)

    def test_fails_closed_on_unverified_source_layout(self):
        for bad in ('', '    section text\n',
                    SOURCE.replace('    section data\n', ''),
                    SOURCE.replace('start:', 'rbc_wrapper_exit:')):
            with self.subTest(bad=bad[:20]):
                with self.assertRaises(NativeWrapperError):
                    wrapper_source(bad, bytes(768))
        with self.assertRaisesRegex(NativeWrapperError, 'font32'):
            wrapper_source(SOURCE, bytes(767))
        with self.assertRaisesRegex(NativeWrapperError, 'stack'):
            assemble_link(SOURCE, bytes(768), stack=True)


if __name__ == '__main__':
    unittest.main()

"""Symbolic Z80 whole-program and native ras/rld regression checks."""
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import ras, rld
from symbolic_z80 import SymbolicError, SymbolicProgram


class SymbolicTests(unittest.TestCase):
    def example(self):
        p = SymbolicProgram()
        p.label('start', entry=True)
        p.instruction('ld a,0')
        p.instruction('or b')
        p.instruction('jp nz,done')
        p.instruction('ld hl,buffer')
        p.instruction('ret')
        p.label('done', entry=True)
        p.instruction('ret')
        p.section('data')
        p.label('table')
        p.reference('done')
        p.binary(bytes([0xC3, 0x00, 0x76, 0xFF, 0x18]))
        p.section('bss')
        p.label('buffer')
        p.reserve(8)
        return p

    def test_symbolic_entries_and_data_are_preserved(self):
        p = self.example()
        text = p.assembly()
        self.assertIn('    dw done\n', text)
        self.assertIn('    db 195,0,118,255,24\n', text)
        self.assertIn('    global done\n', text)
        self.assertNotIn('    db 62,0', text)

    def test_native_link_recomputes_addresses_after_shortening(self):
        p = self.example()
        # The optimizer receives code, data, and entry symbols in ONE call.
        called = []
        def optimizer(asm):
            called.append(asm)
            return asm.replace('    ld a,0\n    or b\n', '    xor a\n    or b\n')
        ssx, stats = p.optimize(optimizer, ras, rld)
        self.assertEqual(len(called), 1)
        parsed = rld.parse_ssx(ssx)
        self.assertEqual(stats['saved_file_bytes'], 1)
        self.assertEqual(parsed['bss'], 8)
        self.assertEqual(parsed['image'][-5:], bytes([0xC3, 0, 0x76, 0xFF, 0x18]))
        self.assertEqual(len(parsed['relocs']), 3)  # branch, buffer and data table
        image = parsed['image']
        # The two uses of the entry symbol and the BSS pointer were
        # resolved again AFTER instruction removal.
        self.assertEqual(int.from_bytes(image[3:5], 'little'), 9)
        self.assertEqual(int.from_bytes(image[6:8], 'little'), len(image))
        self.assertEqual(int.from_bytes(image[10:12], 'little'), 9)

    def test_unsafe_change_to_data_fails(self):
        p = self.example()
        def optimizer(asm):
            return asm.replace('    db 195,0,118,255,24', '    db 195,0,118,255,25')
        with self.assertRaisesRegex(SymbolicError, 'protected data'):
            p.optimize(optimizer, ras, rld)

    def test_internal_branch_label_cannot_disappear(self):
        p = self.example()
        with self.assertRaisesRegex(SymbolicError, 'protected data'):
            p.optimize(lambda x: x.replace('buffer:', ''), ras, rld)

    def test_internal_table_label_cannot_move(self):
        p = self.example()
        def move(asm):
            return asm.replace('table:\n    dw done\n',
                               '    dw done\ntable:\n')
        with self.assertRaisesRegex(SymbolicError, 'protected data'):
            p.optimize(move, ras, rld)

    def test_external_entry_cannot_disappear(self):
        p = self.example()
        with self.assertRaises(SymbolicError):
            p.optimize(lambda x: x.replace('done:', ''), ras, rld)

    def test_optimizer_cannot_inject_layout_directives(self):
        p = self.example()
        for directive in ("org 0", "equ 1", "include 'other.asm'"):
            with self.subTest(directive=directive):
                def insert(asm):
                    return asm.replace("    ld a,0\n", "    " + directive + "\n    ld a,0\n")
                with self.assertRaisesRegex(SymbolicError, 'directive'):
                    p.optimize(insert, ras, rld)

    def test_optimizer_cannot_emit_code_inside_data_or_bss(self):
        p = self.example()
        with self.assertRaisesRegex(SymbolicError, 'non-Z80 code'):
            p.optimize(lambda asm: asm.replace('table:\n', 'table:\n    nop\n'), ras, rld)
        with self.assertRaisesRegex(SymbolicError, 'non-Z80 code'):
            p.optimize(lambda asm: asm.replace('buffer:\n', 'buffer:\n    ret\n'), ras, rld)

    def test_optimizer_can_keep_comments_in_text(self):
        p = self.example()
        ssx, metrics = p.optimize(lambda asm: asm.replace('    ret\n', '    ret ; kept\n'), ras, rld)
        self.assertEqual(metrics['saved_file_bytes'], 0)
        self.assertTrue(ssx.startswith(b'SSX1'))

    def test_no_growth_keeps_original(self):
        p = self.example()
        ssx, stats = p.optimize(lambda x: x, ras, rld)
        self.assertEqual(stats['saved_file_bytes'], 0)
        self.assertEqual(len(ssx), stats['baseline_file_bytes'])

    def test_limits_measured_after_link(self):
        p = self.example()
        with self.assertRaisesRegex(SymbolicError, 'requires'):
            p.optimize(lambda x: x, ras, rld, max_memory=1)

    def test_no_executable_data_confusion(self):
        p = SymbolicProgram()
        p.label('start', entry=True)
        p.instruction('ret')
        p.section('data')
        p.binary(bytes((0xC3, 0x18, 0x00)))
        with self.assertRaisesRegex(SymbolicError, 'text'):
            p.instruction('xor a')

    def test_missing_symbols_and_duplicate_labels(self):
        p = SymbolicProgram()
        with self.assertRaises(SymbolicError):
            p.assembly()
        p.label('start', entry=True)
        with self.assertRaises(SymbolicError):
            p.label('START')


if __name__ == '__main__':
    unittest.main()

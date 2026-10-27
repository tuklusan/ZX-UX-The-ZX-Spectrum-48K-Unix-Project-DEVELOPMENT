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
        self.assertEqual(stats['saved_file_bytes'], 0)
        self.assertFalse(stats['optimizer_admitted'])
        self.assertFalse(stats['candidate_behavior_verified'])
        self.assertEqual(stats['optimizer_candidate_file_bytes'], len(ssx) - 1)
        self.assertEqual(parsed['bss'], 8)
        self.assertEqual(parsed['image'][-5:], bytes([0xC3, 0, 0x76, 0xFF, 0x18]))
        self.assertEqual(len(parsed['relocs']), 3)  # branch, buffer and data table
        image = parsed['image']
        # The linked baseline retains the exact original address layout.
        self.assertEqual(int.from_bytes(image[4:6], 'little'), 10)
        self.assertEqual(int.from_bytes(image[7:9], 'little'), len(image))
        self.assertEqual(int.from_bytes(image[11:13], 'little'), 10)
        # The separately linked candidate still has its new addresses, but
        # it is not returned as a runtime-proven executable.
        candidate_obj = ras.assemble_text(optimizer(p.assembly()), 'candidate.s')
        candidate, *_ = rld.link([rld.Obj(candidate_obj, 'candidate.sso')], [],
                                 entry='start', stack=384)
        new_image = rld.parse_ssx(candidate)['image']
        self.assertEqual(int.from_bytes(new_image[3:5], 'little'), 9)
        self.assertEqual(int.from_bytes(new_image[6:8], 'little'), len(new_image))
        self.assertEqual(int.from_bytes(new_image[10:12], 'little'), 9)

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

    def test_optimizer_cannot_move_instructions_across_binary_resource(self):
        p = SymbolicProgram()
        p.label('start', entry=True)
        p.instruction('jp execution')
        p.binary(bytes((0xc3,)))
        p.label('execution')
        p.instruction('ld a,0')
        p.instruction('ret')
        with self.assertRaisesRegex(SymbolicError, 'protected resource boundary'):
            p.optimize(lambda asm: asm.replace('    jp execution\n    db 195\n',
                                               '    db 195\n    jp execution\n'),
                       ras, rld)
        binary, sizes = p.optimize(lambda asm: asm, ras, rld)
        self.assertEqual(sizes['saved_file_bytes'], 0)
        self.assertEqual(rld.parse_ssx(binary)['image'][3], 0xc3)

    def test_native_candidate_growth_remains_measured_but_unpublished(self):
        p = self.example()
        baseline, baseline_stats = p.optimize(lambda asm: asm, ras, rld)
        changed, stats = p.optimize(
            lambda asm: asm.replace('    ld a,0\n', '    ld hl,0\n'),
            ras, rld)
        self.assertEqual(changed, baseline)
        self.assertFalse(stats['optimizer_admitted'])
        self.assertGreater(stats['optimizer_candidate_file_bytes'], len(baseline))
        self.assertGreater(stats['optimizer_candidate_memory_bytes'],
                           baseline_stats['baseline_memory_bytes'])
        self.assertEqual(stats['optimized_file_bytes'], len(baseline))
        self.assertEqual(stats['saved_file_bytes'], 0)
        self.assertEqual(stats['saved_memory_bytes'], 0)

    def test_native_candidate_exact_dimensions_even_without_savings(self):
        p = self.example()
        binary, stats = p.optimize(lambda asm: asm, ras, rld)
        parsed = rld.parse_ssx(binary)
        self.assertFalse(stats['optimizer_admitted'])
        self.assertEqual(stats['optimizer_candidate_file_bytes'], len(binary))
        self.assertEqual(stats['optimizer_candidate_image_bytes'], len(parsed['image']))
        self.assertEqual(stats['optimizer_candidate_bss_bytes'], parsed['bss'])
        self.assertEqual(stats['optimizer_candidate_stack_bytes'], parsed['stack'])
        self.assertEqual(stats['optimizer_candidate_total_bytes'],
                         len(parsed['image']) + parsed['bss'] + parsed['stack'])
        self.assertEqual(stats['optimizer_candidate_memory_bytes'],
                         stats['baseline_memory_bytes'])

    def test_smaller_candidate_remains_unpublished_without_behavior_proof(self):
        p = self.example()
        baseline, _ = p.optimize(lambda asm: asm, ras, rld)
        binary, stats = p.optimize(
            lambda asm: asm.replace('    ld a,0\n', '    xor a\n'),
            ras, rld)
        self.assertEqual(binary, baseline)
        self.assertFalse(stats['optimizer_admitted'])
        self.assertFalse(stats['candidate_behavior_verified'])
        self.assertLess(stats['optimizer_candidate_file_bytes'], len(binary))
        self.assertLess(stats['optimizer_candidate_memory_bytes'],
                        stats['optimized_memory_bytes'])
        self.assertEqual(stats['saved_file_bytes'], 0)

    def test_native_shorter_register_load_changes_carry_at_three_bases(self):
        from z80_python.cpu import Z80CPU
        p = SymbolicProgram()
        p.label('start', entry=True)
        p.instruction('scf')
        p.instruction('ld a,0')
        p.instruction('ret')
        baseline, _ = p.optimize(lambda asm: asm, ras, rld)
        rejected, stats = p.optimize(
            lambda asm: asm.replace('    ld a,0\n', '    xor a\n'),
            ras, rld)
        self.assertEqual(rejected, baseline)
        self.assertFalse(stats['optimizer_admitted'])
        optimized_obj = ras.assemble_text(
            p.assembly().replace('    ld a,0\n', '    xor a\n'), 'flags.s')
        optimized, *_ = rld.link([rld.Obj(optimized_obj, 'flags.sso')], [],
                                 entry='start', stack=384)
        for base in (0x7000, 0x8000, 0x9000):
            for ssx, carry in ((baseline, 1), (optimized, 0)):
                with self.subTest(base=base, expected_carry=carry):
                    parsed = rld.parse_ssx(ssx)
                    memory = bytearray(65536)
                    image = rld.relocate(parsed['image'], parsed['relocs'], base)
                    memory[base:base + len(image)] = image
                    memory[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
                    cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
                    cpu.pc, cpu.sp = base + parsed['entry'], 0xd000
                    for _ in range(10):
                        if cpu.pc == 0xb000:
                            break
                        cpu.step()
                    else:
                        self.fail('native flag probe did not return')
                    self.assertEqual(cpu.a, 0)
                    self.assertEqual(int(cpu.f) & 1, carry)

    def test_no_growth_keeps_original(self):
        p = self.example()
        ssx, stats = p.optimize(lambda x: x, ras, rld)
        self.assertEqual(stats['saved_file_bytes'], 0)
        self.assertEqual(len(ssx), stats['baseline_file_bytes'])

    def test_exact_native_size_dimensions(self):
        p = self.example()
        raw, sizes = p.optimize(lambda asm: asm, ras, rld)
        linked = rld.parse_ssx(raw)
        self.assertEqual(sizes['baseline_file_bytes'], len(raw))
        self.assertEqual(sizes['optimized_file_bytes'], len(raw))
        for prefix in ('baseline', 'optimized'):
            self.assertEqual(sizes[prefix + '_stack_bytes'], 384)
            self.assertEqual(sizes[prefix + '_image_bytes'], len(linked['image']))
            self.assertEqual(sizes[prefix + '_bss_bytes'], linked['bss'])
            self.assertEqual(sizes[prefix + '_total_bytes'],
                             len(linked['image']) + linked['bss'] + linked['stack'])
            self.assertEqual(sizes[prefix + '_memory_bytes'],
                             max(len(raw), sizes[prefix + '_total_bytes']))

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

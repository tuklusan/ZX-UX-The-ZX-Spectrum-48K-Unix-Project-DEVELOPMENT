"""Relative source branch labels and native Z80 relocation regressions."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
from symbolic_relative_branches import (RelativeBranchError,
                                        inspect_relative_branches,
                                        verify_three_relative_passes)
from symbolic_z80 import SymbolicProgram
import ras
import rld


def span(start, end, text, kind='instruction'):
    return SimpleNamespace(start=start, end=end, source=text, kind=kind)


def source_asm(text):
    table = {'jr nz,-3': b'\x20\xfd', 'jr z,+1': b'\x28\x01',
             'jr +2': b'\x18\x02', 'djnz -4': b'\x10\xfc',
             'jr c,$02': b'\x38\x02', 'jr nc,0x02': b'\x30\x02'}
    return table[text]


class RelativeSources(unittest.TestCase):
    def test_backward_jr_and_assembled_label(self):
        parts = [span(0, 2, 'ld b,3'), span(2, 3, 'dec b'),
                 span(3, 5, 'jr nz,-3'), span(5, 6, 'ret')]
        got = inspect_relative_branches(parts, 6, source_asm)
        self.assertEqual(got[3].target, 2)
        self.assertEqual(got[3].opcode, 'jr nz')
        p = SymbolicProgram()
        p.label('start', entry=True)
        p.instruction('ld b,3')
        p.label('source_0002')
        p.instruction('dec b')
        p.instruction('jr nz,source_0002')
        p.instruction('ret')
        obj = ras.assemble_text(p.assembly(), 'source-relative.s')
        image, _, _, _, _ = rld.link([rld.Obj(obj, 'source-relative.sso')], [],
                                      entry='start', stack=384)
        self.assertEqual(rld.parse_ssx(image)['image'][:6],
                         bytes((6, 3, 5, 0x20, 0xfd, 0xc9)))

    def test_forward_branch_to_next_source_boundary(self):
        parts = [span(0, 2, 'jr +2'), span(2, 4, 'ld a,1'),
                 span(4, 5, 'ret')]
        self.assertEqual(inspect_relative_branches(parts, 5, source_asm)[0].target, 4)

    def test_djnz_is_resolved_from_source_offset(self):
        parts = [span(0, 2, 'ld b,4'), span(2, 4, 'djnz -4'),
                 span(4, 5, 'ret')]
        self.assertEqual(inspect_relative_branches(parts, 5, source_asm)[2].target, 0)

    def test_forward_hex_displacement(self):
        parts = [span(0, 2, 'jr c,$02'), span(2, 4, 'ld a,0'),
                 span(4, 5, 'ret')]
        self.assertEqual(inspect_relative_branches(parts, 5, source_asm)[0].target, 4)
        parts[0] = span(0, 2, 'jr nc,0x02')
        self.assertEqual(inspect_relative_branches(parts, 5, source_asm)[0].target, 4)

    def test_target_inside_data_cannot_be_repaired(self):
        parts = [span(0, 2, 'jr z,+1'), span(2, 3, 'nop'),
                 span(3, 4, 'defb $76', 'inline-data'), span(4, 5, 'ret')]
        with self.assertRaisesRegex(RelativeBranchError, 'not a source instruction'):
            inspect_relative_branches(parts, 5, source_asm)

    def test_jump_to_middle_of_instruction_rejected(self):
        parts = [span(0, 2, 'jr z,+1'), span(2, 5, 'ld hl,1'),
                 span(5, 6, 'ret')]
        with self.assertRaises(RelativeBranchError):
            inspect_relative_branches(parts, 6, source_asm)

    def test_jump_past_code_into_data_rejected(self):
        parts = [span(0, 2, 'jr +2'), span(2, 4, 'ld a,1'),
                 span(4, 5, 'DATA', 'data-source')]
        with self.assertRaises(RelativeBranchError):
            inspect_relative_branches(parts, 4, source_asm)

    def test_illegal_conditions_and_unknown_operands_rejected(self):
        for source in ('jr po,+1', 'jr nz,label', 'djnz 128',
                       'jr z,-129', 'djnz +', 'jr z,+1,+2'):
            with self.subTest(source=source), self.assertRaises(RelativeBranchError):
                inspect_relative_branches([span(0, 2, source)], 2, source_asm)

    def test_fake_source_displacement_encoding_rejected(self):
        with self.assertRaisesRegex(RelativeBranchError, 'encoding differs'):
            inspect_relative_branches([span(0, 2, 'jr +2'),
                                       span(2, 4, 'ld a,2'), span(4, 5, 'ret')],
                                      5, lambda source: b'\x18\x03')

    def test_original_relative_opcode_byte_must_match_the_source(self):
        sources = (
            ('jr +2', b'\x20\x02'),
            ('jr nz,-3', b'\x18\xfd'),
            ('jr z,+1', b'\x30\x01'),
            ('jr c,$02', b'\x28\x02'),
            ('jr nc,0x02', b'\x38\x02'),
            ('djnz -4', b'\x18\xfc'),
        )
        for source, wrong_encoding in sources:
            with self.subTest(source=source):
                with self.assertRaisesRegex(RelativeBranchError,
                                            'branch encoding differs'):
                    inspect_relative_branches(
                        [span(0, 2, source), span(2, 3, 'nop'),
                         span(3, 4, 'ret'), span(4, 5, 'ret')],
                        5, lambda _: wrong_encoding)

    def test_three_native_base_branch_targets_are_identical(self):
        spans = [span(0, 2, 'ld b,3'), span(2, 3, 'dec b'),
                 span(3, 5, 'jr nz,-3'), span(5, 6, 'ret')]
        groups = [inspect_relative_branches(spans, 6, source_asm) for _ in range(3)]
        report = verify_three_relative_passes(groups, [0xdd71, 0xdbec, 0xdb08])
        self.assertEqual(report['verified_relative_branches'], 1)
        self.assertEqual(report['verified_relative_instruction_bytes'], 2)
        self.assertEqual(report['verified_native_bases'], 3)

    def test_three_base_mismatch_is_blocked(self):
        spans = [span(0, 2, 'jr +2'), span(2, 4, 'ld a,1'), span(4, 5, 'ret')]
        groups = [inspect_relative_branches(spans, 5, source_asm) for _ in range(3)]
        groups[2] = {0: groups[2][0].__class__(0, 2, 'jr +2', 'jr')}
        with self.assertRaisesRegex(RelativeBranchError, 'changed across bases'):
            verify_three_relative_passes(groups, [0xdd71, 0xdbec, 0xdb08])

    def test_same_load_base_is_not_three_base_proof(self):
        with self.assertRaisesRegex(RelativeBranchError, 'distinct'):
            verify_three_relative_passes([{}, {}, {}], [0x8000] * 3)

    def test_reoptimized_native_assembler_recalculates_jr(self):
        p = SymbolicProgram()
        p.label('start', entry=True)
        p.instruction('ld b,3')
        p.label('loop')
        p.instruction('ld a,0')
        p.instruction('dec b')
        p.instruction('jr nz,loop')
        p.instruction('ret')
        p.section('data')
        p.binary(b'\xc3\x18\x00')
        plain, _ = p.optimize(lambda a: a, ras, rld)
        better, sizes = p.optimize(lambda a: a.replace('    ld a,0\n',
                                                       '    xor a\n'), ras, rld)
        old = rld.parse_ssx(plain)['image']
        self.assertEqual(plain, better)
        self.assertEqual(old[:8], b'\x06\x03\x3e\x00\x05\x20\xfb\xc9')
        self.assertFalse(sizes['optimizer_admitted'])
        self.assertEqual(sizes['saved_file_bytes'], 0)
        self.assertEqual(sizes['saved_memory_bytes'], 0)
        self.assertEqual(sizes['optimizer_candidate_file_bytes'], len(plain) - 1)
        obj = ras.assemble_text(p.assembly().replace('    ld a,0\n',
                                                      '    xor a\n'), 'short-jr.s')
        candidate, *_ = rld.link([rld.Obj(obj, 'short-jr.sso')], [],
                                 entry='start', stack=384)
        new = rld.parse_ssx(candidate)['image']
        self.assertEqual(new[:7], b'\x06\x03\xaf\x05\x20\xfc\xc9')
        self.assertEqual(old[-3:], new[-3:])


if __name__ == '__main__':
    unittest.main()

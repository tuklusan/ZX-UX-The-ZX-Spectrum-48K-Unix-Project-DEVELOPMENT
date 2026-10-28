"""Only fully sourced Z80 becomes relocatable native assembly."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

STAGE = Path(__file__).resolve().parents[1] / 'stage'
ROOT = STAGE.parents[2]
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
from symbolic_from_source import (UnresolvedSourceProgram,
                                  _validate_static_instruction, from_source)
import ras
import rld


def e(kind, site, payload, source='', target=None):
    return SimpleNamespace(kind=kind, position=site, data=payload,
                           source=source, symbol_offset=target)


def asm(text):
    return {
        'nop': b'\x00', 'ret': b'\xc9',
        'jp 24576': b'\xc3\x00\x60',
        'JP 24576': b'\xc3\x00\x60',
        'jp 24578': b'\xc3\x02\x60',
        'jp 24832': b'\xc3\x00\x61',
        'jp 24577': b'\xc3\x01\x60',
        'jp 24833': b'\xc3\x01\x61',
        'ld hl,241': b'\x21\xf1\x00',
        'ld hl,24584': b'\x21\x08\x60',
        'rst $28': b'\xef', 'defb $31,$04,$38': b'\x31\x04\x38',
        'rst $28; defb $31,$04,$38': b'\xef\x31\x04\x38',
    }[text]


def program(base=0x6000, target=0):
    return [e('instruction', 0, b'\x00', 'nop'),
            e('opcode', 1, b'\xc3', 'jp nn'),
            e('relocation', 2, (base + target).to_bytes(2, 'little'),
              str(target), target),
            e('data-source', 4, b'\xc3\x76', 'BASIC DATA')]


class NativeFromSource(unittest.TestCase):
    def test_link_source_branch_and_preserve_protected_resource(self):
        base = 0x6000
        src = program(base)
        image = b'\x00\xc3\x00\x60\xc3\x76'
        ir = from_source(src, image, base, 4, 8, asm)
        assembly = ir.assembly()
        self.assertIn('jp start', assembly)
        self.assertIn('db 195,118', assembly)
        self.assertIn('ds 8', assembly)
        data = ras.assemble_text(assembly, 'verified.s')
        ssx, *_ = rld.link([rld.Obj(data, 'verified.sso')], [], entry='start', stack=384)
        linked = rld.parse_ssx(ssx)
        self.assertEqual(linked['image'][0:2], b'\x00\xc3')
        self.assertEqual(linked['image'][-2:], b'\xc3\x76')
        self.assertEqual(linked['bss'], 8)
        self.assertEqual(linked['stack'], 384)

    def test_uppercase_typed_runtime_relocation_reaches_native_link(self):
        # The original writer may use uppercase ZX mnemonics. Source
        # ownership and native relocation must agree on the same operand.
        sources = program()
        sources[1] = e('opcode', 1, b'\xc3', 'JP NN')
        image = b'\x00\xc3\x00\x60\xc3\x76'
        ir = from_source(sources, image, 0x6000, 4, 8, asm)
        self.assertIn('jp start', ir.assembly())
        binary = ras.assemble_text(ir.assembly(), 'uppercase-runtime.s')
        ssx, *_ = rld.link([rld.Obj(binary, 'uppercase-runtime.sso')], [],
                           entry='start', stack=384)
        linked = rld.parse_ssx(ssx)
        self.assertEqual(linked['image'][1:4], b'\xc3\x00\x00')
        self.assertEqual(linked['image'][4:], image[4:])

    def test_runtime_relocation_rejects_implied_or_quoted_addresses(self):
        for address_source in ('JP NN,NN', 'JP NN_suffix', 'JP "NN"'):
            with self.subTest(source=address_source):
                sources = program()
                sources[1] = e('opcode', 1, b'\xc3', address_source)
                with self.assertRaises(UnresolvedSourceProgram):
                    from_source(sources, b'\x00\xc3\x00\x60\xc3\x76',
                                0x6000, 4, 8, asm)

    def test_refuse_unpaired_opcode(self):
        src = [e('opcode', 0, b'\xc3', 'jp nn'),
               e('binary', 1, b'\x00\x60')]
        with self.assertRaises(UnresolvedSourceProgram):
            from_source(src, b'\xc3\x00\x60', 0x6000, 3, 0, asm)

    def test_refuse_opaque_runtime(self):
        src = [e('runtime-opaque', 0, b'\xc9', 'RT7')]
        with self.assertRaises(UnresolvedSourceProgram):
            from_source(src, b'\xc9', 0x6000, 1, 0, asm)

    def test_refuse_relocation_into_middle_of_instruction(self):
        src = program(0x6000, target=2)
        image = b'\x00\xc3\x02\x60\xc3\x76'
        with self.assertRaises(UnresolvedSourceProgram):
            from_source(src, image, 0x6000, 4, 0, asm)

    def test_refuse_external_entry_inside_data(self):
        with self.assertRaises(UnresolvedSourceProgram):
            from_source(program(), b'\x00\xc3\x00\x60\xc3\x76',
                        0x6000, 4, 0, asm, entry_offsets=(0, 4))

    def test_refuse_missing_emission_and_untyped_control(self):
        with self.assertRaises(UnresolvedSourceProgram):
            from_source([e('instruction', 0, b'\x00', 'nop')],
                        b'\x00\xc9', 0x6000, 2, 0, asm)

    def test_source_relocation_to_bss_slot_uses_linker_symbol(self):
        base = 0x6000
        image = b'\x21\x08\x60\xc9\x01\x02'
        src = [e('opcode', 0, b'\x21', 'ld hl,nn'),
               e('relocation', 1, b'\x08\x60', '8', 8),
               e('instruction', 3, b'\xc9', 'ret'),
               e('data-source', 4, b'\x01\x02', 'BASIC DATA')]
        ir = from_source(src, image, base, 4, 6, asm)
        self.assertIn('ld hl,source_0008', ir.assembly())
        self.assertIn('ds 2', ir.assembly())
        output = ras.assemble_text(ir.assembly(), 'bss-source.s')
        ssx, *_ = rld.link([rld.Obj(output, 'bss-source.sso')], [],
                           entry='start', stack=384)
        linked = rld.parse_ssx(ssx)
        self.assertEqual(linked['image'][0], 0x21)
        self.assertEqual(linked['image'][-2:], b'\x01\x02')
        self.assertEqual(linked['bss'], 6)

    def test_source_data_in_executable_text_is_not_assumed_code(self):
        with self.assertRaises(UnresolvedSourceProgram):
            from_source([e('data-source', 0, b'\xc9', 'BASIC DATA')],
                        b'\xc9', 0x6000, 1, 0, asm)

    def test_untyped_absolute_operands_are_never_passed_to_linker(self):
        for ins in ('ld hl,24576', 'ld a,(24576)', 'ld (0x6000),a',
                    'ld (0x5c36),hl', 'call $6000', 'jp (hl)',
                    'jr z,+1', 'ld bc,$6000'):
            with self.subTest(ins=ins), self.assertRaises(UnresolvedSourceProgram):
                _validate_static_instruction(ins)

    def test_register_and_byte_immediate_forms_are_explicitly_safe(self):
        for ins in ('ret', 'nop', 'ld a,5', 'ld (hl),$ff',
                    'bit 7,h', 'rst $28', 'cp 0', 'or a'):
            with self.subTest(ins=ins):
                _validate_static_instruction(ins)

    def test_protected_data_followed_by_branch_target_has_one_label(self):
        # A verified jump can target the first instruction after opaque data.
        # Its label is owned by that instruction, never by both producers.
        base = 0x6000
        image = b'\xc3\x05\x60\xfe\xed\xc9'
        src = [e('opcode', 0, b'\xc3', 'jp nn'),
               e('relocation', 1, b'\x05\x60', '5', 5),
               e('inline-data', 3, b'\xfe\xed', 'protected:literal'),
               e('instruction', 5, b'\xc9', 'ret')]
        def source_asm(value):
            if value == 'jp 24581':
                return b'\xc3\x05\x60'
            if value == 'ret':
                return b'\xc9'
            raise ValueError(value)
        verified = from_source(src, image, base, len(image), 0, source_asm)
        source = verified.assembly()
        self.assertEqual(source.count('source_0005:'), 1)
        self.assertIn('jp source_0005', source)
        obj = ras.assemble_text(source, 'protected-target.s')
        ssx, *_ = rld.link([rld.Obj(obj, 'protected-target.sso')], [],
                           entry='start', stack=384)
        linked = rld.parse_ssx(ssx)
        self.assertEqual(bytes(rld.relocate(linked['image'], linked['relocs'], base)),
                         image)
        self.assertEqual(linked['relocs'], [1])

    def test_inline_source_data_preserved(self):
        image = b'\xef\x31\x04\x38\xc9'
        src = [e('instruction', 0, b'\xef\x31\x04\x38',
                 'rst $28; defb $31,$04,$38'),
               e('instruction', 4, b'\xc9', 'ret')]
        ir = from_source(src, image, 0x6000, 5, 0, asm)
        self.assertIn('db 49,4,56', ir.assembly())


if __name__ == '__main__':
    unittest.main()

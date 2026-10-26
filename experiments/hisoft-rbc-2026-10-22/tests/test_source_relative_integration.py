"""Build source branches through ownership checks and native ras/rld."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from symbolic_from_source import UnresolvedSourceProgram, from_source


ASM = {'nop': b'\x00', 'dec a': b'\x3d', 'inc a': b'\x3c',
       'jr nz,-3': b'\x20\xfd', 'jr +1': b'\x18\x01',
       'djnz -3': b'\x10\xfd', 'djnz -4': b'\x10\xfc', 'ret': b'\xc9',
       'call 28672': b'\xcd\x00\x70',
       'call $2bf1': b'\xcd\xf1\x2b',
       'jp z,0x0038': b'\xca\x38\x00',
       'jp nz,0x4000': b'\xc2\x00\x40',
       'ld b,3': b'\x06\x03',
       'ld c,255': b'\x0e\xff',
       'ld hl,1': b'\x21\x01\x00',
       'defb $c3': b'\xc3', 'jr z,-1': b'\x28\xff'}


def assembler(src):
    return ASM[src]


def events(*statements):
    pc = 0
    result = []
    for source in statements:
        data = assembler(source)
        result.append(SimpleNamespace(kind='instruction', position=pc,
                                      data=data, source=source))
        pc += len(data)
    return result


def link(p):
    obj = ras.assemble_text(p.assembly(), 'source-relative.s')
    ssx, _, _, _, _ = rld.link([rld.Obj(obj, 'source-relative.sso')], [],
                                entry='start', stack=384)
    return rld.parse_ssx(ssx)


class FullSourceRelative(unittest.TestCase):
    def test_backward_conditional_compiles_from_exact_source(self):
        es = events('nop', 'dec a', 'jr nz,-3', 'ret')
        data = b''.join(e.data for e in es)
        program = from_source(es, data, 0x7000, len(data), 0, assembler)
        text = program.assembly()
        self.assertIn('source_0001:', text)
        self.assertIn('jr nz,source_0001', text)
        self.assertEqual(link(program)['image'], data)

    def test_backward_djnz_compiles_from_exact_source(self):
        es = events('nop', 'djnz -3', 'ret')
        data = b''.join(e.data for e in es)
        program = from_source(es, data, 0x7000, len(data), 0, assembler)
        self.assertIn('djnz start', program.assembly())
        self.assertEqual(link(program)['image'], data)

    def test_forward_short_jump_compiles_from_exact_source(self):
        es = events('jr +1', 'nop', 'ret')
        data = b''.join(e.data for e in es)
        program = from_source(es, data, 0x7000, len(data), 0, assembler)
        self.assertIn('jr source_0003', program.assembly())
        self.assertEqual(link(program)['image'], data)

    def test_branch_into_middle_of_inline_literal_is_rejected(self):
        es = events('jr z,-1', 'ret')
        data = b''.join(e.data for e in es)
        with self.assertRaisesRegex(UnresolvedSourceProgram, 'not a source instruction'):
            from_source(es, data, 0x7000, len(data), 0, assembler)

    def test_unknown_numeric_absolute_branch_is_still_rejected(self):
        es = events('call 28672', 'ret')
        data = b''.join(e.data for e in es)
        with self.assertRaisesRegex(UnresolvedSourceProgram, 'symbolic target'):
            from_source(es, data, 0x7000, len(data), 0, assembler)

    def test_fixed_rom_calls_and_jumps_link_without_relocation(self):
        for source in ('call $2bf1', 'jp z,0x0038'):
            with self.subTest(source=source):
                es = events(source)
                data = b''.join(e.data for e in es)
                program = from_source(es, data, 0x7000, len(data), 0, assembler)
                self.assertEqual(link(program)['image'], data)

    def test_eight_bit_register_immediates_are_source_literals(self):
        for source in ('ld b,3', 'ld c,255'):
            with self.subTest(source=source):
                es = events(source, 'ret')
                data = b''.join(e.data for e in es)
                program = from_source(es, data, 0x7000, len(data), 0, assembler)
                self.assertEqual(link(program)['image'], data)

    def test_untyped_sixteen_bit_immediate_is_not_guessed(self):
        es = events('ld hl,1', 'ret')
        data = b''.join(e.data for e in es)
        with self.assertRaisesRegex(UnresolvedSourceProgram, 'address type'):
            from_source(es, data, 0x7000, len(data), 0, assembler)

    def test_integer_loop_with_numeric_byte_and_relative_jump(self):
        es = events('ld b,3', 'djnz -4', 'ret')
        data = b''.join(e.data for e in es)
        program = from_source(es, data, 0x7000, len(data), 0, assembler)
        self.assertEqual(link(program)['image'], data)
        self.assertIn('djnz start', program.assembly())

    def test_static_calls_outside_rom_remain_blocked(self):
        for source in ('call 28672', 'jp nz,0x4000'):
            with self.subTest(source=source):
                es = events(source)
                data = b''.join(e.data for e in es)
                with self.assertRaisesRegex(UnresolvedSourceProgram, 'symbolic target'):
                    from_source(es, data, 0x7000, len(data), 0, assembler)

    def test_runtime_opaque_bytes_are_never_promoted(self):
        es = events('ret')
        es.append(SimpleNamespace(kind='runtime-opaque', position=1,
                                  data=b'\xc9', source='RT1'))
        with self.assertRaisesRegex(UnresolvedSourceProgram, 'unresolved source bytes'):
            from_source(es, b'\xc9\xc9', 0x7000, 2, 0, assembler)


if __name__ == '__main__':
    unittest.main()

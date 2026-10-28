"""Quoted DB resources are not compiler-owned Z80 code pointers."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stage"))
from gate8_typed_cfg_liveness import inspect_typed_cfg_liveness, TypedCFGError


class QuotedDataCFGTests(unittest.TestCase):
    def test_quoted_source_data_does_not_invent_address_taken_entries(self):
        import ras
        import rld
        # Literal resource bytes may contain semicolons, commas, and the
        # spelling of a private code label. None is a code pointer.
        source = ('    section text\n    global start\nstart:\n'
                  '    ret\nhandler:\n    ld a,42\n    ret\n'
                  '    section data\n'
                  '    db "handler;ignored,handler",67 ; handler is comment\n'
                  '    defb \'handler,handler;again\'\n')
        result = inspect_typed_cfg_liveness(source)
        self.assertEqual(result['instruction_count'], 3)
        self.assertEqual(result['direct_cfg_reachable_instructions'], 1)
        self.assertEqual(result['unreached_instructions'], 2)
        self.assertEqual(result['unresolved_pointer_expressions'], 0)
        self.assertFalse(result['unknown_entry_reachability'])
        self.assertFalse(result['rewrite_safe_to_admit'])
        obj = ras.assemble_text(source, 'quoted-native.s')
        ssx, *_ = rld.link([rld.Obj(obj, 'quoted-native.sso')], [],
                           entry='start', stack=384)
        parsed = rld.parse_ssx(ssx)
        self.assertEqual(parsed['image'],
                         b'\xc9\x3e\x2a\xc9handler;ignored,handlerC'
                         b'handler,handler;again')
        for base in (0x6000, 0x7000, 0x8000):
            with self.subTest(base=base):
                from z80_python.cpu import Z80CPU
                ram = bytearray(65536)
                actual = rld.relocate(parsed['image'], parsed['relocs'], base)
                self.assertEqual(actual, parsed['image'])
                ram[base:base + len(actual)] = actual
                ram[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
                cpu = Z80CPU(ram.__getitem__, ram.__setitem__)
                cpu.pc, cpu.sp = base + parsed['entry'], 0xd000
                cpu.step()
                self.assertEqual(cpu.pc, 0xb000)
                self.assertEqual(cpu.sp, 0xd002)
                self.assertEqual(ram[base:base + len(actual)], actual)

    def test_symbolic_byte_operand_outside_quotes_remains_opaque(self):
        source = ('section text\nstart:\n    ret\n'
                  'handler:\n    ld a,42\n    ret\n'
                  'section data\n'
                  '    db "handler,notapointer",<handler ; comment\n')
        report = inspect_typed_cfg_liveness(source)
        self.assertEqual(report['unresolved_pointer_expressions'], 1)
        self.assertTrue(report['unknown_entry_reachability'])
        self.assertEqual(report['reachable_instructions'], 3)

    def test_unclosed_quoted_data_cannot_hide_source_comments(self):
        with self.assertRaisesRegex(TypedCFGError, 'unterminated quoted'):
            inspect_typed_cfg_liveness(
                'section text\nstart:\n ret\n'
                'section data\n db "unterminated;label\n')


if __name__ == "__main__":
    unittest.main()

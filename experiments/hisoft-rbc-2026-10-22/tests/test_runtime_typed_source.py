"""Original runtime producer sites must own every emitted byte."""
from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from runtime_typed_source import (RuntimeStatement, RuntimeSourceError,
                                  typed_runtime_events)


@dataclass(frozen=True)
class Write:
    position: int
    value: int
    emitter_pc: int | None


def assemble(source):
    mapping = {'ld a,1': b'\x3e\x01', 'ret': b'\xc9',
               'defb $76': b'\x76', 'jp 28678': b'\xc3\x06\x70'}
    return mapping[source]


def fixture():
    image = b'\x3e\x01\xc9\x76'
    sources = (RuntimeStatement(0, 0x7001, 'instruction', 'ld a,1'),
               RuntimeStatement(2, 0x7008, 'instruction', 'ret'),
               RuntimeStatement(3, 0x7010, 'literal', 'defb $76'))
    writes = [Write(i, v, (0x7001 if i < 2 else 0x7008 if i == 2 else 0x7010))
              for i, v in enumerate(image)]
    return image, sources, writes


class RuntimeTypedSources(unittest.TestCase):
    def test_instruction_and_protected_literal_have_source_owners(self):
        image, source, writes = fixture()
        events = typed_runtime_events(writes, source, image, 0, 4, 0x7000, assemble)
        self.assertEqual([(e.kind, e.source) for e in events],
                         [('instruction', 'ld a,1'), ('instruction', 'ret'),
                          ('inline-data', 'defb $76')])
        self.assertEqual(b''.join(e.data for e in events), image)
        self.assertEqual(events[-1].source, 'defb $76')

    def test_absolute_relocation_is_explicit_and_native(self):
        import ras
        import rld
        source = (RuntimeStatement(0, 0x7011, 'relocated', 'jp nn', 6),
                  RuntimeStatement(3, 0x7012, 'instruction', 'ret'),
                  RuntimeStatement(4, 0x7013, 'literal', 'defb $76'),
                  RuntimeStatement(5, 0x7014, 'instruction', 'ret'))
        # At base 0x7000 the fourth instruction is at relative offset 5;
        # the relocation intentionally targets offset 6 in program storage.
        image = b'\xc3\x06\x70\xc9\x76\xc9\x00'
        source += (RuntimeStatement(6, 0x7015, 'literal', 'defb 0'),)
        def encoder(text):
            if text == 'defb 0':
                return b'\0'
            return assemble(text)
        writes = [Write(i, b, 0x7011 if i < 3 else 0x7012 if i == 3
                        else 0x7013 if i == 4 else 0x7014 if i == 5 else 0x7015)
                  for i, b in enumerate(image)]
        events = typed_runtime_events(writes, source, image, 0, 7, 0x7000, encoder)
        self.assertEqual([(e.kind, e.position) for e in events[:2]],
                         [('opcode', 0), ('relocation', 1)])
        self.assertEqual(events[1].symbol_offset, 6)
        obj = ras.assemble_text('    section text\n    global start\nstart:\n'
                                '  jp target\n  ret\n  db $76\n  ret\n'
                                'target:\n  db 0\n', 'rt-native.s')
        ssx, *_ = rld.link([rld.Obj(obj, 'rt-native.sso')], [], entry='start', stack=384)
        linked = rld.parse_ssx(ssx)
        self.assertEqual(linked['image'][:1], b'\xc3')
        self.assertEqual(linked['image'][3:], image[3:])
        self.assertEqual(linked['image'][1:3], b'\x06\x00')  # native link base is zero

    def test_multi_pc_relocation_preserves_each_original_byte_site(self):
        from symbolic_emit_sites import inspect_emit_sites, verify_three_emit_sites
        bases = [0x6000, 0x5e1e, 0x5d3a]
        groups = []
        source = (RuntimeStatement(0, 0x7110, 'relocated', 'jp nn', 7,
                                   (0x7110, 0x7120, 0x7130)),)
        for base in bases:
            image = b'\xc3' + (base + 7).to_bytes(2, 'little')
            writes = tuple(Write(i, image[i], source[0].write_pcs[i])
                           for i in range(3))
            encoder = lambda text, expected='jp '+str(base + 7), data=image: (
                data if text == expected else bytes())
            events = typed_runtime_events(writes, source, image,
                                          0, 3, base, encoder)
            sites = inspect_emit_sites(events)
            self.assertEqual(sites[0].producer_pcs, (0x7110,))
            self.assertEqual(sites[1].producer_pcs, (0x7120, 0x7130))
            groups.append(sites)
        result = verify_three_emit_sites(groups, bases)
        self.assertEqual(result['source_emissions'], 2)
        self.assertEqual(result['source_call_sites'], 2)
        with self.assertRaises(RuntimeSourceError):
            typed_runtime_events(writes,
                (RuntimeStatement(0, 0x7110, 'relocated', 'jp nn', 7,
                                  (0x7110, 0x7120)),),
                image, 0, 3, base, encoder)
        with self.assertRaises(RuntimeSourceError):
            typed_runtime_events(writes,
                (RuntimeStatement(0, 0x7110, 'relocated', 'jp nn', 7,
                                  (0x7110, 0x7130, 0x7120)),),
                image, 0, 3, base, encoder)

    def test_relocation_can_reference_another_runtime_section_or_bss(self):
        image = b'\xc3\x12\x60'
        sources = (RuntimeStatement(0, 0x7011, 'relocated', 'jp nn', 0x12),)
        writes = (Write(0, 0xc3, 0x7011), Write(1, 0x12, 0x7011),
                  Write(2, 0x60, 0x7011))
        def asm(text):
            return {'jp 24594': image}[text]
        events = typed_runtime_events(writes, sources, image, 0, 3, 0x6000, asm)
        self.assertEqual(events[1].symbol_offset, 0x12)
        with self.assertRaises(RuntimeSourceError):
            typed_runtime_events(writes,
                (RuntimeStatement(0, 0x7011, 'relocated', 'jp nn', 0x10000),),
                image, 0, 3, 0x6000, asm)

    def test_data_directives_and_assembler_pseudo_ops_cannot_become_code(self):
        # A fake source provider can return correct image bytes. Without a
        # mnemonic check it can still disguise protected DATA as executable.
        statements = ('db 201', 'dw 201', 'org 0', 'section text',
                      'global start', 'defb 201', 'defw 201', 'start:')
        for statement in statements:
            with self.subTest(statement=statement), self.assertRaisesRegex(
                    RuntimeSourceError, 'not a Z80 instruction'):
                typed_runtime_events(
                    [Write(0, 0xc9, 0x7001)],
                    [RuntimeStatement(0, 0x7001, 'instruction', statement)],
                    b'\xc9', 0, 1, 0x6000, lambda _: b'\xc9')
        # Source which really declares protected data continues to work.
        events = typed_runtime_events(
            [Write(0, 0xc9, 0x7001)],
            [RuntimeStatement(0, 0x7001, 'literal', 'defb 201')],
            b'\xc9', 0, 1, 0x6000, lambda _: b'\xc9')
        self.assertEqual(events[0].kind, 'inline-data')

    def test_relocation_placeholder_is_a_distinct_source_operand(self):
        base = 0x6000
        image = b'\xc3\x07\x60'
        writes = [Write(i, v, 0x7011) for i, v in enumerate(image)]
        with self.assertRaisesRegex(RuntimeSourceError, 'has no target'):
            typed_runtime_events(
                writes, [RuntimeStatement(0, 0x7011, 'relocated', 'jp nn_suffix', 7)],
                image, 0, 3, base, lambda _: image)
        with self.assertRaisesRegex(RuntimeSourceError, 'not a Z80 instruction'):
            typed_runtime_events(
                writes, [RuntimeStatement(0, 0x7011, 'relocated', 'db nn', 7)],
                image, 0, 3, base, lambda _: image)
        with self.assertRaisesRegex(RuntimeSourceError, 'location or statement invalid'):
            typed_runtime_events(
                writes, [RuntimeStatement(0, 0x7011, 'relocated', 'jp nn\x00', 7)],
                image, 0, 3, base, lambda _: image)
        for bad in ("ld hl,'nn'", 'jp "nn"', 'jp nn,nn'):
            with self.subTest(bad=bad), self.assertRaisesRegex(
                    RuntimeSourceError, 'has no target'):
                typed_runtime_events(
                    writes, [RuntimeStatement(0, 0x7011, 'relocated', bad, 7)],
                    image, 0, 3, base, lambda _: image)
        events = typed_runtime_events(
            writes, [RuntimeStatement(0, 0x7011, 'relocated', 'JP NN', 7)],
            image, 0, 3, base,
            lambda text: image if text == 'JP 24583' else b'')
        self.assertEqual(events[1].symbol_offset, 7)

    def test_missing_duplicate_changed_and_unknown_writer_rejected(self):
        image, source, writes = fixture()
        bad = (writes[:2] + writes[3:], writes + writes[:1],
               [Write(0, 0, 0x7001)] + writes[1:],
               [Write(0, image[0], None)] + writes[1:])
        for case in bad:
            with self.subTest(case=case), self.assertRaises(RuntimeSourceError):
                typed_runtime_events(case, source, image, 0, 4, 0x7000, assemble)

    def test_no_type_inferred_from_complete_byte_trace(self):
        image, source, writes = fixture()
        failures = ((), source[:-1], source[:1] +
                    (RuntimeStatement(2, 0x7008, 'instruction', 'defb $c9'),) + source[2:],
                    source[:1] + (RuntimeStatement(2, 0x7008, 'opaque', 'ret'),) + source[2:],
                    source[:1] + (RuntimeStatement(2, 0x700a, 'instruction', 'ret'),) + source[2:])
        for case in failures:
            with self.subTest(case=case), self.assertRaises(RuntimeSourceError):
                typed_runtime_events(writes, case, image, 0, 4, 0x7000, assemble)


if __name__ == '__main__':
    unittest.main()

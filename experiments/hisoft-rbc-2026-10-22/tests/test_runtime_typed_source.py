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
                          ('instruction', 'defb $76')])
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

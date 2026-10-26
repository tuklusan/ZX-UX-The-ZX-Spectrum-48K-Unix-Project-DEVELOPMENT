"""Prove three-base direct control patches survive native symbolic assembly."""
from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from symbolic_capture import Emission
from symbolic_from_source import from_source
from symbolic_patch_binding import PatchBindingError, bind_three_source_passes
from symbolic_source_boundaries import inspect_source_boundaries


def assembler(s):
    if s == 'jp nn':
        return b'\xc3'
    if s.startswith('jp '):
        return b'\xc3' + int(s[3:]).to_bytes(2, 'little')
    if s == 'nop':
        return b'\x00'
    if s == 'ret':
        return b'\xc9'
    if s.startswith('defw '):
        return int(s[5:]).to_bytes(2, 'little')
    raise ValueError(s)


def fixture(base: int, *, method='st_next', target=4):
    addr = (base + target) & 65535
    bs = addr.to_bytes(2, 'little')
    events = [Emission(0, 'opcode', 'jp nn', b'\xc3'),
              Emission(1, 'word', '(0,)', b'\0\0'),
              Emission(3, 'instruction', 'nop', b'\0'),
              Emission(4, 'instruction', 'ret', b'\xc9'),
              Emission(1, 'direct-write', method, bs[:1]),
              Emission(2, 'direct-write', method, bs[1:])]
    return events, b'\xc3' + bs + b'\0\xc9'


class PatchedSources(unittest.TestCase):
    BASES = (0x6000, 0x5e1e, 0x5d3a)

    def bind(self, callback=None):
        pairs = [fixture(b) for b in self.BASES]
        if callback:
            pairs = [callback(i, b, pair) for i, (b, pair)
                     in enumerate(zip(self.BASES, pairs))]
        events, images = zip(*pairs)
        return bind_three_source_passes(events, images, self.BASES, (5,)*3), images

    def test_control_targets_rebind_to_full_symbolic_native_link(self):
        (groups, report), images = self.bind()
        self.assertEqual(report['verified_source_words'], 1)
        self.assertEqual(report['bound_source_word_bytes'], 2)
        for group, image, base in zip(groups, images, self.BASES):
            self.assertEqual([e.kind for e in group],
                             ['opcode', 'relocation', 'instruction', 'instruction'])
            source = inspect_source_boundaries(group, image, base, 5, 0, assembler)
            self.assertTrue(source.fully_typed)
            program = from_source(group, image, base, 5, 0, assembler)
            self.assertIn('jp source_0004', program.assembly())
            obj = ras.assemble_text(program.assembly(), 'patch-test.s')
            ssx, _, _, _, _ = rld.link([rld.Obj(obj, 'patch-test.sso')], [],
                                       entry='start', stack=384)
            native = rld.parse_ssx(ssx)
            self.assertEqual(native['image'], b'\xc3\x04\x00\x00\xc9')
            self.assertEqual(len(native['relocs']), 1)

    def test_changed_target_in_one_pass_is_refused(self):
        def edit(index, base, pair):
            return fixture(base, target=3) if index == 2 else pair
        with self.assertRaisesRegex(ValueError, 'relocation'):
            self.bind(edit)

    def test_unknown_direct_method_remains_unresolved(self):
        def edit(index, base, pair):
            return fixture(base, method='unreviewed') if index == 2 else pair
        with self.assertRaises(ValueError):
            self.bind(edit)

    def test_opcode_and_patch_must_be_adjacent(self):
        def edit(index, base, pair):
            events, image = pair
            events[0] = replace(events[0], position=10)
            return events, image
        with self.assertRaisesRegex(PatchBindingError, 'adjacent'):
            self.bind(edit)

    def test_rewrite_with_no_original_word_fails(self):
        def edit(index, base, pair):
            events, image = pair
            events[1] = replace(events[1], kind='binary')
            return events, image
        with self.assertRaisesRegex(PatchBindingError, 'whole source word'):
            self.bind(edit)

    def test_unrecorded_overlapping_original_fails(self):
        def edit(index, base, pair):
            events, image = pair
            events.insert(2, Emission(2, 'byte', '0', b'\0'))
            return events, image
        with self.assertRaisesRegex(PatchBindingError, 'overlaps'):
            self.bind(edit)

    def test_byte_rewrite_without_cross_pass_proof_is_refused(self):
        def edit(index, base, pair):
            events, image = pair
            events.append(events[-1])
            return events, image
        with self.assertRaises(ValueError):
            self.bind(edit)

    def test_literal_length_is_opaque_inline_data(self):
        bases = self.BASES
        def make(base):
            return ([Emission(0, 'instruction', 'ret', b'\xc9'),
                     Emission(1, 'word', '(0,)', b'\0\0'),
                     Emission(3, 'instruction', 'ret', b'\xc9'),
                     Emission(1, 'direct-write', 'emit_string_inline', b'\x03'),
                     Emission(2, 'direct-write', 'emit_string_inline', b'\x00')],
                    b'\xc9\x03\x00\xc9')
        events, image = zip(*(make(b) for b in bases))
        resolved, report = bind_three_source_passes(events, image, bases, (4,)*3)
        self.assertEqual(report['word_kinds']['literal-length'], 1)
        for group, code, base in zip(resolved, image, bases):
            kinds = inspect_source_boundaries(group, code, base, 4, 0, assembler)
            self.assertTrue(kinds.fully_typed)
            self.assertEqual(kinds.spans[1].kind, 'inline-data')


if __name__ == '__main__':
    unittest.main()

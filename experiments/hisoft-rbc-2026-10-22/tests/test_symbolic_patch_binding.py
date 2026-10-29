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
from symbolic_patch_binding import (PatchBindingError, _final_source_events,
                                     bind_three_source_passes)
from symbolic_source_boundaries import inspect_source_boundaries


def assembler(s):
    if s == 'call nn':
        return b'\xcd'
    if s.startswith('call '):
        return b'\xcd' + int(s[5:]).to_bytes(2, 'little')
    if s == 'jp nn':
        return b'\xc3'
    for source, opcode in (('jp z,', 0xca), ('jp nz,', 0xc2)):
        if s == source + 'nn':
            return bytes((opcode,))
        if s.startswith(source):
            value = int(s[len(source):], 0)
            return bytes((opcode,)) + value.to_bytes(2, 'little')
    if s.startswith('jp '):
        return b'\xc3' + int(s[3:]).to_bytes(2, 'little')
    if s == 'pop hl':
        return b'\xe1'
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

    def test_discarded_inline_word_is_absent_from_final_three_base_source(self):
        builds = []
        for base in self.BASES:
            operand = (base + 3).to_bytes(2, 'little')
            original = [Emission(0, 'instruction', 'ld hl,0', b'\x21\x00\x00'),
                        Emission(1, 'direct-write', 'emit_string_inline', b'\x01'),
                        Emission(2, 'direct-write', 'emit_string_inline', b'\x00'),
                        Emission(0, 'opcode', 'call nn', b'\xcd'),
                        Emission(1, 'relocation', '3', operand, 3),
                        Emission(3, 'instruction', 'ret', b'\xc9')]
            builds.append((original, b'\xcd' + operand + b'\xc9'))
        bound, report = bind_three_source_passes(
            [b[0] for b in builds], [b[1] for b in builds],
            self.BASES, (4,) * 3)
        self.assertEqual(report['verified_source_words'], 0)
        self.assertEqual(report['superseded_source_emissions'], 3)
        for (events, image), source, base in zip(builds, bound, self.BASES):
            self.assertEqual([e.kind for e in source],
                             ['opcode', 'relocation', 'instruction'])
            mapping = inspect_source_boundaries(source, image, base, 4, 0,
                                                assembler)
            self.assertTrue(mapping.fully_typed)
            assembly = from_source(source, image, base, 4, 0,
                                   assembler).assembly()
            self.assertIn('call source_0003', assembly)
            obj = ras.assemble_text(assembly, 'rewound-inline.s')
            linked, *_ = rld.link([rld.Obj(obj, 'rewound-inline.sso')], [],
                                  entry='start', stack=384)
            ssx = rld.parse_ssx(linked)
            self.assertEqual(bytes(rld.relocate(ssx['image'], ssx['relocs'], base)),
                             image)

    def test_rewound_loop_word_rebinds_to_latest_native_jump(self):
        groups, images = [], []
        for base in self.BASES:
            earlier = (base + 4).to_bytes(2, 'little')
            latest = (base + 3).to_bytes(2, 'little')
            groups.append([
                Emission(0, 'instruction', 'jp nz,$FFFF', b'\xc2\xff\xff'),
                Emission(1, 'direct-write', 'spectrum_for', earlier),
                Emission(0, 'instruction', 'jp nz,$FFFF', b'\xc2\xff\xff'),
                Emission(1, 'direct-write', 'spectrum_pass', latest),
                Emission(3, 'instruction', 'ret', b'\xc9'),
            ])
            images.append(b'\xc2' + latest + b'\xc9')
        bound, report = bind_three_source_passes(groups, images,
                                                 self.BASES, (4,) * 3)
        self.assertEqual(report['verified_source_words'], 1)
        self.assertEqual(report['superseded_source_emissions'], 2)
        for events, image, base in zip(bound, images, self.BASES):
            self.assertEqual([e.kind for e in events],
                             ['opcode', 'relocation', 'instruction'])
            source = from_source(events, image, base, 4, 0,
                                 assembler).assembly()
            self.assertIn('jp nz,source_0003', source)
            obj = ras.assemble_text(source, 'rewound-for.s')
            linked, *_ = rld.link([rld.Obj(obj, 'rewound-for.sso')], [],
                                  entry='start', stack=384)
            parsed = rld.parse_ssx(linked)
            self.assertEqual(bytes(rld.relocate(parsed['image'],
                                                 parsed['relocs'], base)), image)

    def test_three_base_rewind_history_must_agree(self):
        runs = []
        for base in self.BASES:
            operand = (base + 3).to_bytes(2, 'little')
            events = [Emission(0, 'instruction', 'ld hl,0', b'\x21\x00\x00'),
                      Emission(1, 'direct-write', 'emit_string_inline', b'\x01'),
                      Emission(2, 'direct-write', 'emit_string_inline', b'\x00'),
                      Emission(0, 'opcode', 'call nn', b'\xcd'),
                      Emission(1, 'relocation', '3', operand, 3),
                      Emission(3, 'instruction', 'ret', b'\xc9')]
            runs.append((events, b'\xcd' + operand + b'\xc9'))
        runs[-1] = (runs[-1][0][3:], runs[-1][1])
        with self.assertRaisesRegex(PatchBindingError, 'rewrite ownership differs'):
            bind_three_source_passes([pair[0] for pair in runs],
                                     [pair[1] for pair in runs],
                                     self.BASES, (4,) * 3)

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
        with self.assertRaisesRegex(PatchBindingError, 'outside original image'):
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
        with self.assertRaisesRegex(PatchBindingError, 'partial source rewrite'):
            self.bind(edit)

    def test_byte_rewrite_without_cross_pass_proof_is_refused(self):
        def edit(index, base, pair):
            events, image = pair
            events.append(events[-1])
            return events, image
        with self.assertRaises(ValueError):
            self.bind(edit)

    def test_original_inline_forward_jump_patches_become_typed_words(self):
        for source, initial, method, opcode in (
                ('jp z,0', b'\xca\0\0', 'end_of_line', 0xca),
                ('jp nz,$FFFF', b'\xc2\xff\xff', 'st_next', 0xc2)):
            with self.subTest(source=source):
                pairs = []
                for base in self.BASES:
                    word = (base + 4).to_bytes(2, 'little')
                    events = [Emission(0, 'instruction', source, initial,
                                       source_site='st_if:1934'),
                              Emission(3, 'instruction', 'nop', b'\0'),
                              Emission(4, 'instruction', 'ret', b'\xc9'),
                              Emission(1, 'direct-write', method, word[:1]),
                              Emission(2, 'direct-write', method, word[1:])]
                    pairs.append((events, bytes((opcode,)) + word + b'\0\xc9'))
                groups, images = zip(*pairs)
                bound, report = bind_three_source_passes(
                    groups, images, self.BASES, (5,) * 3)
                self.assertEqual(report['verified_source_words'], 1)
                for events, image, base in zip(bound, images, self.BASES):
                    self.assertEqual([e.kind for e in events],
                                     ['opcode', 'relocation', 'instruction', 'instruction'])
                    self.assertEqual(events[0].source, source.rsplit(',', 1)[0] + ',nn')
                    self.assertEqual(events[1].symbol_offset, 4)
                    owned = inspect_source_boundaries(events, image, base, 5, 0, assembler)
                    self.assertTrue(owned.fully_typed)
                    program = from_source(events, image, base, 5, 0, assembler)
                    assembly = program.assembly()
                    self.assertIn('source_0004', assembly)
                    obj = ras.assemble_text(assembly, 'inline-jump.s')
                    output, *_ = rld.link([rld.Obj(obj, 'inline-jump.sso')], [],
                                          entry='start', stack=384)
                    native = rld.parse_ssx(output)
                    self.assertEqual(native['relocs'], [1])
                    self.assertEqual(native['image'],
                                     bytes((opcode,)) + b'\x04\0\0\xc9')

    def test_compound_pop_hl_forward_jump_has_exact_relocation(self):
        # The real HiSoft source emitter produces this four-byte fragment.
        for placeholder in ('$FFFF', '0'):
            groups, images = [], []
            for base in self.BASES:
                patched = (base + 5).to_bytes(2, 'little')
                groups.append([
                    Emission(0, 'instruction', 'pop hl; jp ' + placeholder,
                             b'\xe1\xc3' + (b'\xff\xff' if placeholder == '$FFFF' else b'\0\0')),
                    Emission(4, 'instruction', 'nop', b'\0'),
                    Emission(5, 'instruction', 'ret', b'\xc9'),
                    Emission(2, 'direct-write', 'st_next', patched[:1]),
                    Emission(3, 'direct-write', 'st_next', patched[1:]),
                ])
                images.append(b'\xe1\xc3' + patched + b'\0\xc9')
            bound, report = bind_three_source_passes(groups, images,
                                                      self.BASES, (6,) * 3)
            self.assertEqual(report['verified_source_words'], 1)
            for events, image, base in zip(bound, images, self.BASES):
                self.assertEqual([e.kind for e in events],
                                 ['instruction', 'opcode', 'relocation',
                                  'instruction', 'instruction'])
                source = inspect_source_boundaries(events, image, base, 6, 0,
                                                   assembler)
                self.assertTrue(source.fully_typed)
                text = from_source(events, image, base, 6, 0, assembler).assembly()
                self.assertIn('    pop hl', text)
                self.assertIn('jp source_0005', text)
                obj = ras.assemble_text(text, 'pop-jp.s')
                linked, *_ = rld.link([rld.Obj(obj, 'pop-jp.sso')], [],
                                      entry='start', stack=384)
                parsed = rld.parse_ssx(linked)
                self.assertEqual(parsed['relocs'], [2])
                self.assertEqual(bytes(rld.relocate(parsed['image'], parsed['relocs'], base)),
                                 image)

    def test_compound_pop_hl_forward_jump_fails_closed(self):
        variants = (('push hl; jp $FFFF', b'\xe5\xc3\xff\xff'),
                    ('pop hl; call $FFFF', b'\xe1\xcd\xff\xff'),
                    ('pop hl; jp $FFFF', b'\xe1\xc2\xff\xff'),
                    ('pop hl; jp $FFFF; nop', b'\xe1\xc3\xff\xff'))
        for source, original_bytes in variants:
            groups, images = [], []
            for base in self.BASES:
                data = (base + 5).to_bytes(2, 'little')
                groups.append([
                    Emission(0, 'instruction', source, original_bytes),
                    Emission(4, 'instruction', 'nop', b'\0'),
                    Emission(5, 'instruction', 'ret', b'\xc9'),
                    Emission(2, 'direct-write', 'st_next', data[:1]),
                    Emission(3, 'direct-write', 'st_next', data[1:]),
                ])
                images.append(b'\xe1\xc3' + data + b'\0\xc9')
            with self.subTest(source=source):
                with self.assertRaisesRegex(PatchBindingError, 'whole source word|opcode or placeholder'):
                    bind_three_source_passes(groups, images, self.BASES, (6,) * 3)

    def test_original_forward_jump_opcode_mismatch_is_rejected(self):
        for original in (b'\xc3\0\0', b'\xca\x01\0'):
            groups = []
            images = []
            for base in self.BASES:
                word = (base + 4).to_bytes(2, 'little')
                groups.append([Emission(0, 'instruction', 'jp z,0', original),
                               Emission(3, 'instruction', 'nop', b'\0'),
                               Emission(4, 'instruction', 'ret', b'\xc9'),
                               Emission(1, 'direct-write', 'end_of_line', word[:1]),
                               Emission(2, 'direct-write', 'end_of_line', word[1:])])
                images.append(b'\xca' + word + b'\0\xc9')
            with self.assertRaisesRegex(PatchBindingError, 'opcode or placeholder'):
                bind_three_source_passes(groups, images, self.BASES, (5,) * 3)

    def test_inline_forward_patch_conflicting_emitter_is_rejected(self):
        groups, images = [], []
        for base in self.BASES:
            word = (base + 4).to_bytes(2, 'little')
            groups.append([Emission(0, 'instruction', 'jp z,0', b'\xca\0\0'),
                           Emission(1, 'relocation', '(4,)', word, 4),
                           Emission(3, 'instruction', 'nop', b'\0'),
                           Emission(4, 'instruction', 'ret', b'\xc9'),
                           Emission(1, 'direct-write', 'end_of_line', word[:1]),
                           Emission(2, 'direct-write', 'end_of_line', word[1:])])
            images.append(b'\xca' + word + b'\0\xc9')
        with self.assertRaisesRegex(PatchBindingError, 'partial source rewrite'):
            bind_three_source_passes(groups, images, self.BASES, (5,) * 3)

    def test_rewound_source_is_discarded_only_when_entirely_replaced(self):
        groups, images = [], []
        for base in self.BASES:
            addr = (base + 4).to_bytes(2, 'little')
            groups.append([
                Emission(1, 'relocation', '(4,)', addr, 4),
                Emission(0, 'instruction', 'jp z,0', b'\xca\0\0',
                         source_site='st_if:1934'),
                Emission(3, 'instruction', 'nop', b'\0'),
                Emission(4, 'instruction', 'ret', b'\xc9'),
                Emission(1, 'direct-write', 'end_of_line', addr[:1]),
                Emission(2, 'direct-write', 'end_of_line', addr[1:])])
            images.append(b'\xca' + addr + b'\0\xc9')
        final, report = bind_three_source_passes(groups, images,
                                                  self.BASES, (5,) * 3)
        self.assertEqual(report['superseded_source_emissions'], 1)
        for events in final:
            self.assertEqual([e.kind for e in events],
                             ['opcode', 'relocation', 'instruction', 'instruction'])

    def test_partial_source_rewrite_remains_blocked(self):
        events = [Emission(0, 'instruction', 'jp z,0', b'\xca\0\0'),
                  Emission(1, 'word', '(0,)', b'\0\0')]
        with self.assertRaisesRegex(PatchBindingError, 'partial source rewrite'):
            _final_source_events(events, b'\xca\0\0')

    def test_protected_source_cannot_be_discarded_by_later_writer(self):
        events = [Emission(0, 'data-source', 'original DATA', b'\xc9'),
                  Emission(0, 'instruction', 'ret', b'\xc9')]
        with self.assertRaisesRegex(PatchBindingError, 'protected source'):
            _final_source_events(events, b'\xc9')

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

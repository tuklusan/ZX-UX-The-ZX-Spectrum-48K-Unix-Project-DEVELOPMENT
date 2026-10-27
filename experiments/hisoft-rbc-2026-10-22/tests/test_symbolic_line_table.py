"""Independent source witnesses for the original HiSoft BASIC line table."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras, rld
from symbolic_capture import Emission
from symbolic_line_table import (LineTableError, bind_original_line_table,
                                 bind_three_line_tables)
from symbolic_from_source import from_source
from symbolic_source_boundaries import inspect_source_boundaries
from typed_whole_pipeline import verify_and_build, link_source_pair


def build(base=0x6000, *, pairs=((100, 0),)):
    events = [Emission(0, 'instruction', 'ret', b'\xc9', source_site='emit:1')]
    image = bytearray(b'\xc9')
    for line, offset in pairs:
        position = len(image)
        events.append(Emission(position, 'word', f'({line},)',
                               line.to_bytes(2, 'little'),
                               source_site='emit_line_table:2449'))
        image.extend(line.to_bytes(2, 'little'))
        address = ((base + offset) & 65535).to_bytes(2, 'little')
        events.append(Emission(position + 2, 'relocation', f'({offset},)',
                               address, offset, source_site='emit_line_table:2454'))
        image.extend(address)
    events.append(Emission(len(image), 'word', '(65535,)', b'\xff\xff',
                           source_site='emit_line_table:2455'))
    image.extend(b'\xff\xff')
    return tuple(events), bytes(image)


class OriginalLineTable(unittest.TestCase):
    BASES = (0x6000, 0x6100, 0x6200)

    def test_line_table_preserves_data_and_native_reference(self):
        entries, image = build()
        typed, report = bind_original_line_table(entries, image, 0x6000,
                                                  len(image), 0)
        self.assertEqual([e.kind for e in typed],
                         ['instruction', 'inline-data', 'table-relocated', 'inline-data'])
        self.assertEqual(report['line_pairs'], 1)
        self.assertEqual(report['address_words'], 1)
        self.assertEqual(report['protected_table_bytes'], 6)
        def asm(text):
            if text == 'ret':
                return b'\xc9'
            raise ValueError(text)
        m = inspect_source_boundaries(typed, image, 0x6000, len(image), 0, asm)
        self.assertTrue(m.fully_typed)
        program = from_source(typed, image, 0x6000, len(image), 0, asm)
        text = program.assembly()
        self.assertIn('dw start', text)
        binary = ras.assemble_text(text, 'source-table.s')
        ssx, *_ = rld.link([rld.Obj(binary, 'source-table.sso')], [],
                           entry='start', stack=384)
        parsed = rld.parse_ssx(ssx)
        self.assertEqual(parsed['relocs'], [3])
        self.assertEqual(bytes(rld.relocate(parsed['image'], parsed['relocs'], 0x6000)),
                         image)

    def test_three_pass_full_symbolic_native_link_keeps_table(self):
        def asm(text):
            if text == 'ret':
                return b'\xc9'
            raise ValueError(text)
        builds = [build(base) for base in self.BASES]
        groups, images = zip(*builds)
        owned = verify_and_build(groups, images, self.BASES,
                                 (7,) * 3, (0,) * 3, asm)
        self.assertEqual(owned.source_report['source_line_table']['line_pairs'], 1)
        self.assertEqual(owned.reloc_byte_offsets, frozenset((3, 4)))
        plain, candidate, report = link_source_pair(owned, ras, rld,
                                                    lambda text: text)
        self.assertEqual(plain, candidate)
        self.assertEqual(rld.parse_ssx(plain)['relocs'], [3])
        self.assertFalse(report['native_behavior_verified'])

    def test_source_table_with_no_line_pairs_keeps_sentinel(self):
        entries, image = build(pairs=())
        typed, report = bind_original_line_table(entries, image, 0x6000,
                                                  len(image), 0)
        self.assertEqual(report['line_pairs'], 0)
        self.assertEqual(typed[-1].data, b'\xff\xff')

    def test_three_independent_bases_have_same_symbolic_targets(self):
        pairs = [build(base, pairs=((20, 0), (40, 0))) for base in self.BASES]
        groups, images = zip(*pairs)
        typed, report = bind_three_line_tables(groups, images, self.BASES,
                                                (11,) * 3, (0,) * 3)
        self.assertEqual(report['line_pairs'], 2)
        self.assertEqual([x.symbol_offset for x in typed[0]
                          if x.kind == 'table-relocated'], [0, 0])

    def test_changed_byte_or_line_id_is_rejected(self):
        events, image = build()
        bad = list(events)
        bad[1] = replace(bad[1], data=b'\x60\0')
        with self.assertRaisesRegex(LineTableError, 'BASIC line word'):
            bind_original_line_table(bad, image, 0x6000, len(image), 0)
        bad[1] = replace(events[1], source='(300,)')
        with self.assertRaisesRegex(LineTableError, 'BASIC line word'):
            bind_original_line_table(bad, image, 0x6000, len(image), 0)

    def test_mismatched_address_or_untyped_operand_rejected(self):
        events, image = build()
        bad = list(events)
        bad[2] = replace(bad[2], symbol_offset=9)
        with self.assertRaisesRegex(LineTableError, 'line address'):
            bind_original_line_table(bad, image, 0x6000, len(image), 0)
        bad[2] = replace(events[2], source_site='other:2454')
        with self.assertRaises(LineTableError):
            bind_original_line_table(bad, image, 0x6000, len(image), 0)

    def test_source_sentinel_and_complete_extent_required(self):
        events, image = build()
        with self.assertRaisesRegex(LineTableError, 'sentinel'):
            bind_original_line_table(events[:-1], image[:-2], 0x6000,
                                     len(image)-2, 0)
        bad = list(events)
        bad[-1] = replace(bad[-1], data=b'\xff\x7f')
        with self.assertRaisesRegex(LineTableError, 'marker'):
            bind_original_line_table(bad, image, 0x6000, len(image), 0)
        with self.assertRaisesRegex(LineTableError, 'marker'):
            bind_original_line_table(events, image, 0x6000, len(image) - 1, 0)

    def test_source_relocation_cannot_escape_program_and_bss(self):
        events, image = build()
        with self.assertRaisesRegex(LineTableError, 'line address'):
            bad = list(events)
            bad[2] = replace(bad[2], source='(1000,)', symbol_offset=1000,
                             data=(0x6000+1000).to_bytes(2,'little'))
            bind_original_line_table(bad, image, 0x6000, len(image), 0)

    def test_source_change_between_native_bases_rejected(self):
        builds = [build(b) for b in self.BASES]
        groups, images = [list(p[0]) for p in builds], [p[1] for p in builds]
        groups[2][1] = replace(groups[2][1], source='(101,)', data=b'e\x00')
        images[2] = images[2][:1] + b'e\x00' + images[2][3:]
        with self.assertRaisesRegex(LineTableError, 'changed across'):
            bind_three_line_tables(groups, images, self.BASES,
                                   (len(images[0]),)*3, (0,)*3)

    def test_no_original_table_source_changes_nothing(self):
        events = (Emission(0, 'instruction', 'ret', b'\xc9',
                           source_site='emit:1'),)
        protected, report = bind_original_line_table(events, b'\xc9',
                                                      0x6000, 1, 0)
        self.assertEqual(protected, events)
        self.assertEqual(report['table_count'], 0)


if __name__ == '__main__':
    unittest.main()

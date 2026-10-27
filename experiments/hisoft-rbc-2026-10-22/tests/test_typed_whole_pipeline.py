"""Four checkpoints: compiler sites, patch words, full ownership, native link."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]

import ras
import rld
from symbolic_capture import Emission
from typed_whole_pipeline import (SourcePipelineError, link_source_pair,
                                  verify_and_build)


def assembler(s):
    if s == 'jp nn':
        return b'\xc3'
    if s.startswith('jp '):
        return b'\xc3' + int(s[3:]).to_bytes(2, 'little')
    if s == 'nop':
        return b'\x00'
    if s == 'ret':
        return b'\xc9'
    if s == 'defb 1':
        return b'\x01'
    raise ValueError(s)


def fixture(base, *, mismatched=False):
    addr = base + 4
    word = addr.to_bytes(2, 'little')
    events = (Emission(0, 'opcode', 'jp nn', b'\xc3', source_site='emit_goto:100'),
              Emission(1, 'word', '(0,)', b'\0\0', source_site='emit_word:101'),
              Emission(3, 'instruction', 'nop', b'\0', source_site='emit:102'),
              Emission(4, 'instruction', 'ret', b'\xc9', source_site='emit:103'),
              Emission(1, 'direct-write', 'st_next', word[:1]),
              Emission(2, 'direct-write', 'st_next', word[1:]))
    image = b'\xc3' + word + b'\0\xc9'
    if mismatched:
        image = image[:-1] + b'\0'
    return events, image


class WholePipeline(unittest.TestCase):
    bases = (0x6000, 0x6100, 0x6200)

    def cases(self):
        pairs = [fixture(b) for b in self.bases]
        events, images = zip(*pairs)
        return events, images, self.bases, (5,) * 3, (8,) * 3

    def test_four_stages_link_verified_original_baseline(self):
        result = verify_and_build(*self.cases(), assembler)
        self.assertEqual(result.source_report['passes'], 3)
        self.assertEqual(result.source_report['compiler_call_sites']['source_emissions'], 4)
        self.assertEqual(result.source_report['source_word_patches']['verified_source_words'], 1)
        self.assertEqual(result.source_report['source_boundaries']['source_unresolved_bytes'], 0)
        self.assertEqual(result.reloc_byte_offsets, frozenset((1, 2)))
        self.assertIn('jp source_0004', result.program.assembly())
        plain, opt, report = link_source_pair(result, ras, rld, lambda source: source)
        self.assertEqual(plain, opt)
        self.assertEqual(rld.parse_ssx(plain)['image'][0], 0xc3)
        self.assertEqual(rld.parse_ssx(plain)['bss'], 8)
        self.assertEqual(report['plain']['baseline_bss_bytes'], 8)
        self.assertFalse(report['native_behavior_verified'])

    def test_full_instruction_rewind_passes_native_link(self):
        group = (Emission(0, 'instruction', 'ret', b'\xc9',
                          source_site='emit:100'),
                 Emission(0, 'instruction', 'nop', b'\x00',
                          source_site='emit:101'),
                 Emission(1, 'instruction', 'ret', b'\xc9',
                          source_site='emit:102'))
        source = verify_and_build((group,) * 3, (b'\x00\xc9',) * 3,
                                  self.bases, (2,) * 3, (0,) * 3, assembler)
        self.assertEqual(source.source_report['final_source_fragments']
                         ['instruction_statements'], 2)
        plain, candidate, report = link_source_pair(
            source, ras, rld, lambda text: text)
        self.assertEqual(plain, candidate)
        self.assertEqual(rld.parse_ssx(plain)['image'], b'\x00\xc9')
        self.assertTrue(report['native_links_verified'])

    def test_untyped_byte_after_rewind_is_still_refused(self):
        group = (Emission(0, 'instruction', 'ret', b'\xc9',
                          source_site='emit:100'),
                 Emission(0, 'byte', '(0,)', b'\x00',
                          source_site='emit_byte:101'),
                 Emission(1, 'instruction', 'ret', b'\xc9',
                          source_site='emit:102'))
        with self.assertRaisesRegex(SourcePipelineError, 'unresolved source bytes'):
            verify_and_build((group,) * 3, (b'\x00\xc9',) * 3,
                             self.bases, (2,) * 3, (0,) * 3, assembler)

    def test_replaced_protected_calculator_data_rejected(self):
        group = (Emission(0, 'instruction', 'ret; defb 1', b'\xc9\x01',
                          source_site='emit:100'),
                 Emission(0, 'instruction', 'nop; ret', b'\x00\xc9',
                          source_site='emit:101'))
        with self.assertRaisesRegex(SourcePipelineError, 'protected inline data'):
            verify_and_build((group,) * 3, (b'\x00\xc9',) * 3,
                             self.bases, (2,) * 3, (0,) * 3, assembler)

    def test_partial_historical_instruction_rewrite_rejected(self):
        group = (Emission(0, 'instruction', 'nop; ret', b'\x00\xc9',
                          source_site='emit:100'),
                 Emission(0, 'instruction', 'ret', b'\xc9',
                          source_site='emit:101'))
        with self.assertRaisesRegex(SourcePipelineError, 'partial'):
            verify_and_build((group,) * 3, (b'\xc9\xc9',) * 3,
                             self.bases, (2,) * 3, (0,) * 3, assembler)

    def test_bad_compiler_site_rejected_before_any_link(self):
        events, images, bases, ends, bss = self.cases()
        mutated = list(events[1])
        mutated[0] = replace(mutated[0], source_site='emit_goto:999')
        with self.assertRaisesRegex(SourcePipelineError, 'call sites changed'):
            verify_and_build((events[0], tuple(mutated), events[2]),
                             images, bases, ends, bss, assembler)

    def test_untyped_direct_word_and_corrupt_patch_refused(self):
        events, images, bases, ends, bss = self.cases()
        changed = list(events[0])
        changed[-1] = replace(changed[-1], source='unknown_writer')
        with self.assertRaises(SourcePipelineError):
            verify_and_build((tuple(changed), events[1], events[2]),
                             images, bases, ends, bss, assembler)
        corrupt = list(images)
        corrupt[2] = corrupt[2][:-1] + b'\0'
        with self.assertRaises(SourcePipelineError):
            verify_and_build(events, tuple(corrupt), bases, ends, bss, assembler)

    def test_untyped_runtime_and_changed_storage_refused(self):
        events, images, bases, ends, bss = self.cases()
        changed = [tuple(list(group) + [Emission(4, 'runtime-opaque', 'RT5', b'\xc9')])
                   for group in events]
        with self.assertRaises(SourcePipelineError):
            verify_and_build(changed, images, bases, ends, bss, assembler)
        with self.assertRaisesRegex(SourcePipelineError, 'equal BSS'):
            verify_and_build(events, images, bases, ends, (8, 8, 9), assembler)

    def test_native_plain_mismatch_fails_closed(self):
        result = verify_and_build(*self.cases(), assembler)
        forged = replace(result, compiled_image=result.compiled_image[:3] + b'\xc9\xc9')
        with self.assertRaisesRegex(SourcePipelineError, 'differs outside'):
            link_source_pair(forged, ras, rld, lambda text: text)

    def test_native_optimizer_cannot_mutate_protected_layout(self):
        result = verify_and_build(*self.cases(), assembler)
        with self.assertRaises(ValueError):
            link_source_pair(result, ras, rld,
                             lambda text: text.replace('source_0004:', 'source_0005:'))

    def test_distinct_bases_and_complete_passes_required(self):
        events, images, bases, ends, bss = self.cases()
        with self.assertRaisesRegex(SourcePipelineError, 'three valid'):
            verify_and_build(events[:2], images[:2], bases[:2], ends[:2],
                             bss[:2], assembler)
        with self.assertRaisesRegex(SourcePipelineError, 'three valid'):
            verify_and_build(events, images, (bases[0],)*3, ends, bss, assembler)


if __name__ == '__main__':
    unittest.main()

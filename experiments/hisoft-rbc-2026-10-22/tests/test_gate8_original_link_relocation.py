"""Require native plain links to reproduce the original three-pass bytes."""
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
from typed_whole_pipeline import SourcePipelineError, verify_and_build, link_source_pair


def assembler(text):
    if text == 'jp nn':
        return b'\xc3'
    if text.startswith('jp '):
        return b'\xc3' + int(text[3:]).to_bytes(2, 'little')
    if text == 'nop':
        return b'\x00'
    if text == 'ret':
        return b'\xc9'
    raise ValueError(text)


def original_three_passes():
    bases = (0x6000, 0x6100, 0x6200)
    outputs, images = [], []
    for base in bases:
        address = (base + 4).to_bytes(2, 'little')
        outputs.append((
            Emission(0, 'opcode', 'jp nn', b'\xc3', source_site='emit_goto:100'),
            Emission(1, 'word', '(0,)', b'\x00\x00', source_site='emit_word:101'),
            Emission(3, 'instruction', 'nop', b'\x00', source_site='emit:102'),
            Emission(4, 'instruction', 'ret', b'\xc9', source_site='emit:103'),
            Emission(1, 'direct-write', 'st_next', address[:1]),
            Emission(2, 'direct-write', 'st_next', address[1:]),
        ))
        images.append(b'\xc3' + address + b'\x00\xc9')
    return outputs, images, bases, (5,) * 3, (8,) * 3


class OriginalLinkRelocation(unittest.TestCase):
    def setUp(self):
        self.source = verify_and_build(*original_three_passes(), assembler)

    def test_native_plain_relocations_match_the_original_48k_source(self):
        plain, optimized, report = link_source_pair(
            self.source, ras, rld, lambda source: source)
        self.assertEqual(plain, optimized)
        parsed = rld.parse_ssx(plain)
        self.assertEqual(parsed['relocs'], [1])
        self.assertEqual(parsed['bss'], 8)
        self.assertEqual(self.source.source_report['source_bss_bytes'], 8)
        self.assertEqual(bytes(rld.relocate(
            parsed['image'], parsed['relocs'], self.source.original_base)),
            self.source.compiled_image)
        self.assertFalse(report['native_behavior_verified'])

    def test_wrong_relocation_site_manifest_refused(self):
        invalid = replace(self.source, reloc_byte_offsets=frozenset())
        with self.assertRaisesRegex(SourcePipelineError, 'relocation sites differ'):
            link_source_pair(invalid, ras, rld, lambda source: source)

    def test_wrong_original_base_refused(self):
        invalid = replace(self.source, original_base=0x6300)
        with self.assertRaisesRegex(SourcePipelineError, 'relocated operand differs'):
            link_source_pair(invalid, ras, rld, lambda source: source)

    def test_wrong_original_relocation_operand_refused(self):
        image = bytearray(self.source.compiled_image)
        image[2] ^= 1
        invalid = replace(self.source, compiled_image=bytes(image))
        with self.assertRaisesRegex(SourcePipelineError, 'relocated operand differs'):
            link_source_pair(invalid, ras, rld, lambda source: source)

    def test_bss_mismatch_refused(self):
        invalid = replace(self.source, source_report={
            **self.source.source_report, 'source_bss_bytes': 9})
        with self.assertRaisesRegex(SourcePipelineError, 'storage layout differs'):
            link_source_pair(invalid, ras, rld, lambda source: source)

    def test_nonrelocated_source_byte_mismatch_refused(self):
        image = bytearray(self.source.compiled_image)
        image[3] ^= 1
        invalid = replace(self.source, compiled_image=bytes(image))
        with self.assertRaisesRegex(SourcePipelineError, 'differs outside typed relocation'):
            link_source_pair(invalid, ras, rld, lambda source: source)


if __name__ == '__main__':
    unittest.main()

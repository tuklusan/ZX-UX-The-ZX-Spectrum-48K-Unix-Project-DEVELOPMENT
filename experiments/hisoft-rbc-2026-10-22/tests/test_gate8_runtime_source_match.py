"""Source-origin checks for vendor runtime and separately owned replacements."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
from gate8_original_runtime_types import OriginalEmitter, SourceTransactions, compiler_image
from gate8_original_runtime_layout import _run_emitter
from gate8_runtime_source_match import (RuntimeMatchError,
    verify_runtime_source_match, verify_three_runtime_sources)


class VendorSourceVerification(unittest.TestCase):
    BASES = (0x6000, 0x6100, 0x6200)

    @classmethod
    def setUpClass(cls):
        tape = Path('/mnt/data/HiSoft_BASIC_v1.1_48K_compiler_only.tzx')
        cls.code = compiler_image(tape.read_bytes()) if tape.is_file() else None
        cls.rom = (ROOT / 'src/zx-ux-sdk/rom/48.rom').read_bytes()

    def fixture(self, base, *, override_bytes=b'\x00\x01\x02'):
        machine = OriginalEmitter(self.code, self.rom, base)
        machine.mem[0x4000 + (27 - 1)*3] = 1
        machine.type_source = SourceTransactions(machine.mem, base)
        end = _run_emitter(machine, 27, 0, False)
        vendor = bytes(machine.mem[0x9000:0x9000 + end])
        image = vendor + override_bytes
        spans = [SimpleNamespace(kind='runtime-opaque', source='RT27',
                                 start=0, end=end),
                 SimpleNamespace(kind='runtime-opaque', source='RT43',
                                 start=end, end=len(image))]
        return image, spans, end

    def require_input(self):
        if self.code is None:
            self.skipTest('owner-supplied original compiler tape missing')

    def test_real_vendor_bytes_and_custom_extension_stay_separate(self):
        self.require_input()
        img, spans, end = self.fixture(self.BASES[0])
        report = verify_runtime_source_match(self.code, self.rom, img,
                                           self.BASES[0], spans, {43: 'poke'})
        self.assertEqual(report.report['original_routines_verified'], 1)
        self.assertEqual(report.report['original_source_bytes'], end)
        self.assertEqual(report.report['replacement_source_bytes_untyped'], 3)
        self.assertFalse(report.report['complete_runtime_assembly_verified'])
        self.assertFalse(report.report['native_behavior_verified'])

    def test_three_real_emitter_sources_and_addresses(self):
        self.require_input()
        fixtures = [self.fixture(base) for base in self.BASES]
        result = verify_three_runtime_sources(
            self.code, self.rom, [f[0] for f in fixtures], self.BASES,
            [f[1] for f in fixtures], {43: 'poke'})
        self.assertEqual(result['original_source_bases_verified'], 3)
        self.assertEqual(result['replacement_routines_untyped'], [43])

    def test_altered_vendor_byte_or_extent_fails_closed(self):
        self.require_input()
        img, spans, end = self.fixture(self.BASES[0])
        bad = bytes((img[0] ^ 1,)) + img[1:]
        with self.assertRaisesRegex(RuntimeMatchError, 'original source bytes'):
            verify_runtime_source_match(self.code, self.rom, bad,
                                      self.BASES[0], spans, {43: 'poke'})
        spans[0] = replace_like(spans[0], end=end - 1)
        with self.assertRaises(RuntimeMatchError):
            verify_runtime_source_match(self.code, self.rom, img,
                                      self.BASES[0], spans, {43: 'poke'})

    def test_reserved_emitter_without_override_is_rejected(self):
        self.require_input()
        img, spans, _ = self.fixture(self.BASES[0])
        with self.assertRaisesRegex(RuntimeMatchError, 'no original'):
            verify_runtime_source_match(self.code, self.rom, img,
                                      self.BASES[0], spans, {})

    def test_order_overlap_bad_name_and_repeated_base_rejected(self):
        self.require_input()
        img, spans, end = self.fixture(self.BASES[0])
        spans[1] = replace_like(spans[1], start=end - 1)
        with self.assertRaisesRegex(RuntimeMatchError, 'order or extent'):
            verify_runtime_source_match(self.code, self.rom, img,
                                      self.BASES[0], spans, {43: 'poke'})
        img, spans, end = self.fixture(self.BASES[0])
        spans[1] = replace_like(spans[1], source='not-original')
        with self.assertRaisesRegex(RuntimeMatchError, 'emitter ID'):
            verify_runtime_source_match(self.code, self.rom, img,
                                      self.BASES[0], spans, {43: 'poke'})
        with self.assertRaisesRegex(RuntimeMatchError, 'three distinct'):
            verify_three_runtime_sources(self.code, self.rom,
                                             [img]*3, [self.BASES[0]]*3,
                                             [spans]*3, {43: 'poke'})

    def test_real_bricklayer_three_pass_compiler_source_match(self):
        self.require_input()
        checkpoint = ROOT / 'build/tmp/rbc-latest-checkpoint/rbc'
        frontend = ROOT / 'build/tmp/rbc-g8-frontend-verified'
        tape = ROOT / 'build/tmp/rbc-g8-hisoft-original.tap'
        if not ((checkpoint / 'rbc.py').is_file() and
                (frontend / 'compiler.py').is_file() and tape.is_file()):
            self.skipTest('untracked verified compiler inputs unavailable')
        import gate8_full_source_audit as audit
        result = audit.run(ROOT / 'src/bonus/60-programs/42-bricklayer/BASIC/42-bricklayer.bas',
                           checkpoint, frontend, tape,
                           ROOT / 'src/zx-ux-sdk/rom/48.rom')
        source_report = result['original_runtime_source_match']
        self.assertEqual(source_report['original_routines_verified'], 40)
        self.assertEqual(source_report['original_source_bytes'], 610)
        self.assertEqual(source_report['replacement_routines_untyped'], [])
        self.assertEqual(source_report['typed_replacement_routines_verified'], [43, 55])
        self.assertEqual(source_report['typed_replacement_source_bytes'], 428)
        self.assertEqual(source_report['replacement_source_bytes_untyped'], 0)
        self.assertEqual(source_report['original_source_bases_verified'], 3)
        self.assertFalse(result['whole_program_attempt']['native_link_verified'])


def replace_like(obj, **kwargs):
    return SimpleNamespace(**(vars(obj) | kwargs))


if __name__ == '__main__':
    unittest.main()

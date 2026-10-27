"""Native baseline from original typed source instructions and runtime symbols."""
from __future__ import annotations

from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from symbolic_capture import Emission
from gate8_whole_native_baseline import WholeBaselineError, _source_program
from z80asm import asm


class WholeNativeBaselineTests(unittest.TestCase):
    def test_original_control_target_enters_typed_runtime(self):
        base = 0x6000
        events = (
            Emission(0, 'opcode', 'call nn', b'\xcd'),
            Emission(1, 'relocation', '3', b'\x03\x60', 3),
            Emission(3, 'runtime-opaque', 'RT1', b'\xc9'),
            Emission(4, 'data-source', 'BASIC DATA', b'\xfe'),
        )
        image = b'\xcd\x03\x60\xc9\xfe'
        runtime = (((1, 3, 4),), ('rbc_fake_entry:', '  ret'),
                   {'rbc_fake_entry': 3})
        with patch('gate8_whole_native_baseline._runtime_listing', return_value=runtime):
            source, report, _, section = _source_program(
                events, image, base, 4, 0, asm, b'', b'', {}, {})
        self.assertIn('call source_0003', source)
        self.assertEqual(source.count('source_0003:'), 1)
        self.assertIn('rbc_fake_entry:', source)
        self.assertEqual(section, (3, 4))
        self.assertEqual(report['fixed_or_indirect_instructions_not_type_approved'], 0)
        obj = ras.assemble_text(source, 'whole-source-unit.s')
        ssx, *_ = rld.link([rld.Obj(obj, 'whole-source-unit.sso')], [],
                           entry='start', stack=384)
        info = rld.parse_ssx(ssx)
        self.assertEqual(info['relocs'], [1])
        self.assertEqual(bytes(rld.relocate(info['image'], info['relocs'], base)), image)
        self.assertEqual(info['stack'], 384)

    def test_reject_source_pointer_into_untyped_runtime_byte(self):
        base = 0x6000
        events = (
            Emission(0, 'opcode', 'call nn', b'\xcd'),
            Emission(1, 'relocation', '4', b'\x04\x60', 4),
            Emission(3, 'runtime-opaque', 'RT1', b'\xc9\xc9'),
        )
        runtime = (((1, 3, 5),), ('rbc_fake_entry:', '  ret', '  ret'),
                   {'rbc_fake_entry': 3})
        with patch('gate8_whole_native_baseline._runtime_listing', return_value=runtime):
            with self.assertRaisesRegex(WholeBaselineError, 'target'):
                _source_program(events, b'\xcd\x04\x60\xc9\xc9', base,
                                5, 0, asm, b'', b'', {}, {})

    def test_reject_unresolved_nonruntime_compiler_bytes(self):
        events = (
            Emission(0, 'instruction', 'ret', b'\xc9'),
            Emission(1, 'byte', '(2,)', b'\x02'),
            Emission(2, 'runtime-opaque', 'RT1', b'\xc9'),
        )
        runtime = (((1, 2, 3),), ('rbc_fake_entry:', '  ret'),
                   {'rbc_fake_entry': 2})
        with patch('gate8_whole_native_baseline._runtime_listing', return_value=runtime):
            with self.assertRaisesRegex(WholeBaselineError, 'unresolved bytes'):
                _source_program(events, b'\xc9\x02\xc9', 0x6000, 3, 0,
                                asm, b'', b'', {}, {})

    def test_byte_mismatch_cannot_be_accepted_as_native_source(self):
        events = (
            Emission(0, 'instruction', 'ret', b'\xc9'),
            Emission(1, 'runtime-opaque', 'RT1', b'\xc9'),
        )
        runtime = (((1, 1, 2),), ('rbc_fake_entry:', '  ret'),
                   {'rbc_fake_entry': 1})
        with patch('gate8_whole_native_baseline._runtime_listing', return_value=runtime):
            with self.assertRaises(WholeBaselineError):
                _source_program(events, b'\xc9\x00', 0x6000, 2, 0,
                                asm, b'', b'', {}, {})

    def test_real_originals_three_native_bases(self):
        compiler = os.environ.get('RBC_G8_CHECKPOINT')
        frontend = os.environ.get('RBC_G8_FRONTEND')
        tape = os.environ.get('RBC_G8_TAPE')
        if not all((compiler, frontend, tape)):
            self.skipTest('requires recovered original compiler and fixed frontend revision')
        from gate8_full_source_audit import run
        for game in ('42-bricklayer', '28-dam-busters', '56-roots'):
            with self.subTest(game=game):
                report = run(ROOT / f'src/bonus/60-programs/{game}/BASIC/{game}.bas',
                             Path(compiler), Path(frontend), Path(tape),
                             ROOT / 'src/zx-ux-sdk/rom/48.rom')
                full = report['native_whole_source_baseline']
                self.assertTrue(full['native_whole_source_baseline_linked'])
                self.assertEqual(full['native_source_bases'], 3)
                self.assertTrue(full['native_image_byte_exact'])
                self.assertTrue(full['all_source_relocations_verified'])
                self.assertFalse(full['full_program_optimized'])
                self.assertFalse(full['native_behavior_verified'])
                self.assertLessEqual(max(full['native_file_bytes'],
                                         full['native_total_bytes']), 12000)


if __name__ == '__main__':
    unittest.main()

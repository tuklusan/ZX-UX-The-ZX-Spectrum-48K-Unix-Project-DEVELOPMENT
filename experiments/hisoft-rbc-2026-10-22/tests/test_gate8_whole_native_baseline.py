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

    def test_source_pointer_into_relocated_call_operand_is_native_exact(self):
        # This is typed source, not a reconstruction from disassembled bytes.
        # The first instruction obtains the *data address* of the CALL word.
        for base in (0x6000, 0x7000, 0x8000):
            with self.subTest(base=base):
                events = (
                    Emission(0, 'opcode', 'ld hl,nn', b'\x21'),
                    Emission(1, 'relocation', '4', (base + 4).to_bytes(2, 'little'), 4),
                    Emission(3, 'opcode', 'call nn', b'\xcd'),
                    Emission(4, 'relocation', '6', (base + 6).to_bytes(2, 'little'), 6),
                    Emission(6, 'runtime-opaque', 'RT1', b'\xc9'),
                    Emission(7, 'data-source', 'BASIC DATA', b'\xfe'),
                )
                image = (b'\x21' + (base + 4).to_bytes(2, 'little') +
                         b'\xcd' + (base + 6).to_bytes(2, 'little') + b'\xc9\xfe')
                runtime = (((1, 6, 7),), ('rbc_fake_entry:', '  ret'),
                           {'rbc_fake_entry': 6})
                with patch('gate8_whole_native_baseline._runtime_listing',
                           return_value=runtime):
                    source, counts, _, _ = _source_program(
                        events, image, base, 7, 0, asm, b'', b'', {}, {})
                self.assertIn('source_0003:', source)
                self.assertIn('ld hl,source_0003+1', source)
                self.assertIn('call source_0006', source)
                self.assertNotIn('db 33', source)  # Preserve the typed LD mnemonic.
                obj = ras.assemble_text(source, 'whole-operand-pointer.s')
                ssx, *_ = rld.link([rld.Obj(obj, 'whole-operand-pointer.sso')],
                                   [], entry='start', stack=384)
                result = rld.parse_ssx(ssx)
                self.assertEqual(result['relocs'], [1, 4])
                self.assertEqual(bytes(rld.relocate(result['image'],
                                                    result['relocs'], base)), image)
                self.assertEqual(counts['source_emitter_instructions'], 2)

    def test_control_branch_into_immediate_operand_still_rejected(self):
        base = 0x6000
        # The same interior byte is forbidden as an executable CALL target.
        events = (
            Emission(0, 'opcode', 'call nn', b'\xcd'),
            Emission(1, 'relocation', '4', b'\x04\x60', 4),
            Emission(3, 'opcode', 'ld hl,nn', b'\x21'),
            Emission(4, 'relocation', '6', b'\x06\x60', 6),
            Emission(6, 'runtime-opaque', 'RT1', b'\xc9'),
        )
        runtime = (((1, 6, 7),), ('rbc_fake_entry:', '  ret'),
                   {'rbc_fake_entry': 6})
        image = b'\xcd\x04\x60\x21\x06\x60\xc9'
        with patch('gate8_whole_native_baseline._runtime_listing',
                   return_value=runtime):
            with self.assertRaisesRegex(WholeBaselineError,
                                        'control relocation target'):
                _source_program(events, image, base, 7, 0, asm,
                                b'', b'', {}, {})

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

    def test_optimizer_resource_rejection_preserves_original_native_proof(self):
        required = tuple(os.environ.get(name) for name in (
            'RBC_G8_CHECKPOINT', 'RBC_G8_FRONTEND', 'RBC_G8_TAPE',
            'RBC_G8_OPTIMIZER'))
        if not all(required):
            self.skipTest('exact compiler and optimizer sources required')
        from gate8_full_source_audit import run
        game = '23-biorhythms'
        source = ROOT / 'src/bonus/60-programs' / game / 'BASIC' / (game + '.bas')
        report = run(source, Path(required[0]), Path(required[1]),
                     Path(required[2]), ROOT / 'src/zx-ux-sdk/rom/48.rom')
        baseline = report['native_whole_source_baseline']
        self.assertTrue(baseline['native_whole_source_baseline_linked'])
        self.assertTrue(baseline['native_image_byte_exact'])
        self.assertTrue(baseline['all_source_relocations_verified'])
        self.assertEqual(baseline['native_source_bases'], 3)
        candidate = baseline['native_whole_optimizer_candidate']
        self.assertIn('protected resource boundary', candidate['blocker'])
        self.assertFalse(candidate['native_candidate_link_verified'])
        self.assertFalse(candidate['optimizer_candidate_admitted_for_publication'])
        self.assertEqual(candidate['native_baseline_sha256'], baseline['native_sha256'])
        self.assertFalse(report['gate8_complete'])

    def test_real_originals_three_native_bases(self):
        compiler = os.environ.get('RBC_G8_CHECKPOINT')
        frontend = os.environ.get('RBC_G8_FRONTEND')
        tape = os.environ.get('RBC_G8_TAPE')
        if not all((compiler, frontend, tape)):
            self.skipTest('requires recovered original compiler and fixed frontend revision')
        from gate8_full_source_audit import run
        for game in ('42-bricklayer', '28-dam-busters', '56-roots',
                     '03-tug-of-war'):
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

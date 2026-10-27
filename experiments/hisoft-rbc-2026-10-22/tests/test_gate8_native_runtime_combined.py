"""Native multi-emitter linking with protected original ROM calculator bytes."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]

from gate8_native_runtime_combined import (
    RuntimeCombinedError, _ROM_CALCULATOR, _original_z80_and_calculator,
    _runtime_spans, _replacement_listing, _vendor_listing, native_runtime_region,
    verify_three_native_runtime_regions, VendorSection,
)
from gate8_original_runtime_types import compiler_image, OriginalEmitter, SourceTransactions
from spectrum_runtime import guarded_val_bytes
from gate8_original_runtime_layout import _run_emitter
from z80_python.disasm import disassemble_bytes


class OriginalSourceSections(unittest.TestCase):
    def fixture(self, number):
        if number == 72:
            data = bytes.fromhex('ef 09 38 22 65 5c 23 23 6e 26 00 c9')
        else:
            data = bytes.fromhex(
                'ed 4b 76 5c cd 2b 2d ef a1 0f 34 37 16 04 34 80 41'
                ' 00 00 80 32 02 a1 03 31 38 cd a2 2d ed 43 76 5c'
                ' 7e a7 28 03 d6 10 77 c9')
        start = 0
        return data, tuple((index, byte, 0x8000+index)
                           for index, byte in enumerate(data))

    def test_original_calculator_bytecodes_are_protected_data(self):
        for n in (72, 127):
            with self.subTest(n=n):
                data, writes = self.fixture(n)
                ops, protected = _original_z80_and_calculator(n, writes, 0x6000, 0)
                start, whole = _ROM_CALCULATOR[n]
                self.assertEqual(protected, {start+1: whole[1:]})
                self.assertEqual(ops[start].text, 'RST 0x28')
                self.assertEqual(ops[start].data, b'\xef')
                self.assertTrue(all(i not in ops for i in
                                    range(start+1,start+len(whole))))
                self.assertEqual(sum(op.size for op in ops.values())+
                                 sum(len(raw) for raw in protected.values()),len(data))
                self.assertIn(len(data)-1, ops)

    def test_changed_bytecodes_and_copy_sources_are_rejected(self):
        for n in (72,127):
            data, writes = self.fixture(n)
            start, bytecode = _ROM_CALCULATOR[n]
            modified = list(writes)
            site = start+1
            modified[site] = (site, modified[site][1] ^ 1, modified[site][2])
            with self.subTest(n=n,kind='byte'):
                with self.assertRaisesRegex(RuntimeCombinedError, 'calculator source'):
                    _original_z80_and_calculator(n, modified, 0x6000, 0)
            modified = list(writes)
            modified[site] = (site, modified[site][1], None)
            with self.subTest(n=n,kind='source'):
                with self.assertRaisesRegex(RuntimeCombinedError, 'calculator source'):
                    _original_z80_and_calculator(n, modified, 0x6000, 0)

    def test_unclassified_calculator_source_is_rejected(self):
        data, writes = self.fixture(72)
        with self.assertRaisesRegex(RuntimeCombinedError, 'unclassified'):
            _original_z80_and_calculator(73, writes, 0x6000, 0)

    def test_runtime_selection_rejects_reordering_or_overlap(self):
        a=SimpleNamespace(kind='runtime-opaque',source='RT72',start=5,end=17)
        b=SimpleNamespace(kind='runtime-opaque',source='RT127',start=17,end=58)
        self.assertEqual(_runtime_spans((a,b), bytes(58)),((72,5,17),(127,17,58)))
        for wrong in (SimpleNamespace(kind='runtime-opaque',source='RT127',start=16,end=58),
                      SimpleNamespace(kind='runtime-opaque',source='RT70',start=17,end=58),
                      SimpleNamespace(kind='runtime-opaque',source='RT128',start=17,end=59)):
            with self.subTest(value=wrong):
                with self.assertRaises(RuntimeCombinedError):
                    _runtime_spans((a,wrong), bytes(58))

    def test_guarded_val_is_native_source_and_fail_closed(self):
        from rtnames import RT
        expected = guarded_val_bytes()
        self.assertEqual(len(expected), 122)
        lines, sites = _replacement_listing(RT.VAL, 500, 0x6000, {}, expected)
        self.assertEqual(sites, ())
        self.assertEqual(lines[0], 'rbc_val_entry:')
        self.assertTrue(any('rbc_val_blocked:' == line for line in lines))
        changed = bytearray(expected)
        changed[44] ^= 1
        with self.assertRaisesRegex(RuntimeCombinedError, 'guarded VAL source'):
            _replacement_listing(RT.VAL, 500, 0x6000, {}, bytes(changed))
        with self.assertRaisesRegex(RuntimeCombinedError, 'untyped replacement'):
            _replacement_listing(999, 500, 0x6000, {}, expected)

    def test_selected_native_replacement_must_still_be_source_owned(self):
        from rtnames import RT
        span = SimpleNamespace(kind='runtime-opaque',
                               source=f'RT{RT.PAUSE}', start=0, end=1)
        with self.assertRaisesRegex(RuntimeCombinedError,
                                    'complete typed replacement sources'):
            native_runtime_region(b'', b'', b'\xc9', 0x6000,
                                  (span,), {}, {})

    def test_bad_three_pass_parameters_fail_closed(self):
        for bases in ((0x6000,0x6000,0x6200),(0x6000,0x6100)):
            with self.subTest(bases=bases):
                with self.assertRaisesRegex(RuntimeCombinedError, 'three distinct'):
                    verify_three_native_runtime_regions(
                        b'',b'', [b'']*3, bases, [()]*3, {}, [{}]*3)


class LinkedOriginalRegion(unittest.TestCase):
    def test_original_bricklayer_reassembles_every_selected_runtime(self):
        tape = Path('/mnt/data/HiSoft_BASIC_v1.1_48K_compiler_only.tzx')
        checkpoint = ROOT / 'build/tmp/rbc-latest-checkpoint/rbc'
        frontend = ROOT / 'build/tmp/rbc-g8-frontend-verified'
        original_tap = ROOT / 'build/tmp/rbc-g8-hisoft-original.tap'
        if not (tape.is_file() and (checkpoint / 'rbc.py').is_file() and
                (frontend / 'compiler.py').is_file() and original_tap.is_file()):
            self.skipTest('original frontend/tape checkpoint not available')
        import gate8_full_source_audit as audit
        result = audit.run(ROOT / 'src/bonus/60-programs/42-bricklayer/BASIC/42-bricklayer.bas',
                           checkpoint,frontend,original_tap,
                           ROOT / 'src/zx-ux-sdk/rom/48.rom')
        region = result['native_runtime_region']
        self.assertTrue(region['native_region_verified'])
        self.assertEqual(region['passes'], 3)
        self.assertEqual((region['routines'],region['original_routines'],
                          region['replacement_routines']), (42,40,2))
        self.assertEqual(region['runtime_bytes'], 1038)
        self.assertEqual(region['original_relocations'],18)
        self.assertEqual(region['all_relocations'],58)
        self.assertEqual(region['total_region_storage_bytes'], 1422)
        self.assertEqual(region['native_file_bytes'],1116)
        self.assertFalse(region['full_program_optimized'])
        self.assertFalse(result['gate8_complete'])
        self.assertFalse(result['whole_program_attempt']['native_link_verified'])

    def test_original_roots_reassembles_val_and_poke_together(self):
        import os
        checkpoint = Path(os.environ.get('RBC_G8_CHECKPOINT',
                               ROOT / 'build/tmp/rbc-latest-checkpoint/rbc'))
        frontend = Path(os.environ.get('RBC_G8_FRONTEND',
                             ROOT / 'build/tmp/rbc-g8-frontend-verified'))
        original_tap = Path(os.environ.get('RBC_G8_TAPE',
                                 ROOT / 'build/tmp/rbc-g8-hisoft-original.tap'))
        if not ((checkpoint / 'rbc.py').is_file() and
                (frontend / 'compiler.py').is_file() and original_tap.is_file()):
            self.skipTest('original frontend/tape checkpoint not available')
        import gate8_full_source_audit as audit
        root = ROOT / 'src/bonus/60-programs/56-roots/BASIC/56-roots.bas'
        result = audit.run(root, checkpoint, frontend, original_tap,
                           ROOT / 'src/zx-ux-sdk/rom/48.rom')
        region = result['native_runtime_region']
        self.assertTrue(region['native_region_verified'])
        self.assertEqual(region['passes'], 3)
        self.assertEqual((region['routines'], region['original_routines'],
                          region['replacement_routines']), (46, 44, 2))
        self.assertEqual(region['runtime_bytes'], 1083)
        self.assertEqual(region['all_relocations'], 60)
        self.assertEqual(region['native_file_bytes'], 1165)
        self.assertFalse(region['full_program_optimized'])
        self.assertFalse(result['gate8_complete'])
        self.assertFalse(result['whole_program_attempt']['native_link_verified'])


class NativeOriginalOnlyAndFourteenKilobyteTests(unittest.TestCase):
    """Use unchanged corpus sources and the independently checked compiler."""

    def original(self, game):
        import os
        checkpoint = Path(os.environ.get('RBC_G8_CHECKPOINT',
                                   ROOT / 'build/tmp/rbc-latest-checkpoint/rbc'))
        frontend = Path(os.environ.get('RBC_G8_FRONTEND',
                                 ROOT / 'build/tmp/rbc-g8-frontend-verified'))
        tape = Path(os.environ.get('RBC_G8_TAPE',
                             ROOT / 'build/tmp/rbc-g8-hisoft-original.tap'))
        if not ((checkpoint / 'rbc.py').is_file() and
                (frontend / 'compiler.py').is_file() and tape.is_file()):
            self.skipTest('locked HiSoft source and original tape required')
        from gate8_full_source_audit import run
        source = ROOT / f'src/bonus/60-programs/{game}/BASIC/{game}.bas'
        return run(source, checkpoint, frontend, tape,
                   ROOT / 'src/zx-ux-sdk/rom/48.rom')

    def test_critical_path_original_only_runtime_native_relinks(self):
        report = self.original('07-critical-path-analysis')
        region = report['native_runtime_region']
        self.assertTrue(region['native_region_verified'])
        self.assertEqual(region['passes'], 3)
        self.assertEqual((region['routines'],region['original_routines'],
                          region['replacement_routines']), (46, 46, 0))
        self.assertEqual(region['runtime_bytes'], 653)
        self.assertEqual(region['all_relocations'], 21)
        full = report['native_whole_source_baseline']
        self.assertTrue(full['native_whole_source_baseline_linked'])
        self.assertTrue(full['native_image_byte_exact'])
        self.assertTrue(full['all_source_relocations_verified'])
        self.assertEqual(full['native_source_bases'], 3)
        self.assertEqual(full['native_total_bytes'], 13180)
        self.assertEqual(full['native_file_bytes'], 11293)
        self.assertFalse(full['full_program_optimized'])
        self.assertFalse(full['native_behavior_verified'])
        self.assertFalse(report['gate8_complete'])

    def test_fall_guy_and_chomper_14k_native_source_limit(self):
        for game, expected_file, expected_memory in (
                ('02-fall-guy', 12765, 12664),
                ('08-chomper', 12829, 12087)):
            with self.subTest(game=game):
                report = self.original(game)
                full = report['native_whole_source_baseline']
                self.assertTrue(full['native_whole_source_baseline_linked'])
                self.assertTrue(full['native_image_byte_exact'])
                self.assertTrue(full['all_source_relocations_verified'])
                self.assertEqual(full['native_source_bases'], 3)
                self.assertEqual(full['native_file_bytes'], expected_file)
                self.assertEqual(full['native_total_bytes'], expected_memory)
                self.assertGreater(max(expected_file, expected_memory), 12000)
                self.assertLessEqual(max(expected_file, expected_memory), 14000)
                self.assertFalse(full['full_program_optimized'])
                self.assertFalse(full['native_behavior_verified'])
                self.assertFalse(report['gate8_complete'])


    def test_original_14k_whole_source_compiler_and_optimizer_pairs(self):
        """Lock native relinks across three bases without calling gameplay proven."""
        expected = (
            ('11-defend', 13343, 13013),
            ('57-bulls-and-cows', 5388, 5543),
            ('58-invaders', 11937, 12761),
            ('60-countabout', 11898, 11862),
        )
        import os
        if not os.environ.get('RBC_G8_OPTIMIZER'):
            self.skipTest('locked source optimizer required for candidate audit')
        for game, size, total in expected:
            with self.subTest(game=game):
                report = self.original(game)
                full = report['native_whole_source_baseline']
                self.assertTrue(full['native_whole_source_baseline_linked'])
                self.assertTrue(full['native_image_byte_exact'])
                self.assertTrue(full['all_source_relocations_verified'])
                self.assertEqual(full['native_source_bases'], 3)
                self.assertEqual(full['native_file_bytes'], size)
                self.assertEqual(full['native_total_bytes'], total)
                self.assertLessEqual(max(size, total), 14000)
                candidate = full['native_whole_optimizer_candidate']
                self.assertTrue(candidate['native_candidate_link_verified'])
                self.assertTrue(candidate['candidate_byte_identical'])
                self.assertEqual(candidate['candidate_file_bytes_saved'], 0)
                self.assertEqual(candidate['native_baseline_sha256'],
                                 candidate['native_candidate_sha256'])
                self.assertFalse(candidate['optimizer_candidate_admitted_for_publication'])
                self.assertFalse(candidate['native_behavior_verified'])
                self.assertFalse(full['full_program_optimized'])
                self.assertFalse(report['gate8_complete'])


if __name__ == '__main__':
    unittest.main()

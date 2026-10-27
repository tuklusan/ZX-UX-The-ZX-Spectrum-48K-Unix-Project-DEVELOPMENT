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
    _runtime_spans, _replacement_listing, _vendor_listing,
    verify_three_native_runtime_regions, VendorSection,
)
from gate8_original_runtime_types import compiler_image, OriginalEmitter, SourceTransactions
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


if __name__ == '__main__':
    unittest.main()

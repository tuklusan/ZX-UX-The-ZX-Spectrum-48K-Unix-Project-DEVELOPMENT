"""Native instruction reassembly checks use the operator's original tape."""
from pathlib import Path
import sys
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from gate8_original_runtime_native import (
    BASES, RuntimeNativeError, audit_original_native, native_reassemble,
    source_assembly,
)
from gate8_original_runtime_types import OriginalEmitter, compiler_image


class NativeSourceAssembly(unittest.TestCase):
    def test_real_instruction_assembly_is_symbolic(self):
        computed = []
        writes = [(0, 0x21, 0x7000), (1, 1, 0x7001), (2, 0, 0x7002),
                  (3, 0xC9, 0x7003)]
        assembly, reloc = source_assembly(computed, writes, BASES[0])
        self.assertIn('ld hl, 0x0001', assembly.lower())
        self.assertIn('ret', assembly.lower())
        self.assertNotIn('db ', assembly.lower())
        self.assertEqual(reloc, {})

    def test_unknown_relocation_address_refused(self):
        from types import SimpleNamespace
        low = SimpleNamespace(kind='reloc-low', position=1, target_offset=20)
        high = SimpleNamespace(kind='reloc-high', position=2, target_offset=20)
        writes = [(0, 0xC3, None), (1, 0x14, None), (2, 0x60, None)]
        with self.assertRaisesRegex(RuntimeNativeError, 'another original runtime'):
            source_assembly([low, high], writes, BASES[0])

    def test_missing_high_relocation_refused(self):
        from types import SimpleNamespace
        low = SimpleNamespace(kind='reloc-low', position=1, target_offset=0)
        writes = [(0, 0xC3, None), (1, 0, None), (2, 0x60, None)]
        with self.assertRaisesRegex(RuntimeNativeError, 'incomplete'):
            source_assembly([low], writes, BASES[0])


class OriginalNativeEmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tape = Path('/mnt/data/HiSoft_BASIC_v1.1_48K_compiler_only.tzx')
        cls.tape = tape.read_bytes() if tape.is_file() else None
        cls.rom = (STAGE.parents[2] / 'src/zx-ux-sdk/rom/48.rom').read_bytes()

    def test_real_native_three_base_reassembly(self):
        if self.tape is None:
            self.skipTest('original vendor tape must be supplied')
        data = audit_original_native(self.tape, self.rom)
        self.assertEqual(data['original_runtime_emitters'], 121)
        self.assertEqual(data['linked_routines'], 118)
        self.assertEqual(data['linked_image_bytes'], 1335)
        self.assertEqual(data['linked_file_bytes'], 3783)
        self.assertEqual(data['relocation_sites'], 50)
        self.assertEqual([x['routine'] for x in data['unresolved']], [72, 88, 99])
        self.assertTrue(all('relative jump out of range' in x['reason']
                            for x in data['unresolved']))
        self.assertFalse(data['cross_routine_layout_verified'])
        self.assertFalse(data['full_program_runtime_equivalence_verified'])
        self.assertFalse(data['gate8_complete'])

    def test_source_relocation_is_native_linked_at_three_bases(self):
        if self.tape is None:
            self.skipTest('original vendor tape must be supplied')
        code = compiler_image(self.tape)
        native = [native_reassemble(OriginalEmitter(code, self.rom, base).run(2),
                                    code, self.rom, base)
                  for base in BASES]
        self.assertEqual(len({x['output_sha256'] for x in native}), 1)
        self.assertEqual(native[0]['relocation_sites'], 1)
        self.assertEqual(native[0]['image_bytes'], 9)


if __name__ == '__main__':
    unittest.main()

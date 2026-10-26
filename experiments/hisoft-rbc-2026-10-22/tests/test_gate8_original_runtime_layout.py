"""Original Z80 dependency selection and grouped native runtime tests."""
from pathlib import Path
import sys
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from gate8_original_runtime_layout import (
    BASES, RuntimeLayoutError, original_layout, verify_selected_runtimes,
)
from gate8_original_runtime_types import compiler_image


class InputValidation(unittest.TestCase):
    def test_reject_missing_routines(self):
        with self.assertRaisesRegex(RuntimeLayoutError, 'invalid'):
            original_layout(b'', b'', [], BASES[0])

    def test_reject_out_of_range_ids(self):
        with self.assertRaisesRegex(RuntimeLayoutError, 'invalid'):
            original_layout(b'', b'', [132], BASES[0])

    def test_reject_noninteger_ids(self):
        with self.assertRaisesRegex(RuntimeLayoutError, 'invalid'):
            original_layout(b'', b'', ['2'], BASES[0])

    def test_all_native_bases_must_be_distinct(self):
        with self.assertRaisesRegex(RuntimeLayoutError, 'three distinct'):
            verify_selected_runtimes(b'', b'', [2], (BASES[0], BASES[0], BASES[2]))


class RealOriginalSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tape = Path('/mnt/data/HiSoft_BASIC_v1.1_48K_compiler_only.tzx')
        cls.tape = tape.read_bytes() if tape.is_file() else None
        cls.rom = (STAGE.parents[2] / 'src/zx-ux-sdk/rom/48.rom').read_bytes()

    def test_original_runtime_dependency_closure(self):
        if self.tape is None:
            self.skipTest('original vendor tape absent')
        report = verify_selected_runtimes(self.tape, self.rom, [99])
        self.assertEqual(report['selected_routines'], [99, 100, 101, 102, 105])
        self.assertEqual(report['native']['image_bytes'], 92)
        self.assertEqual(report['native']['file_bytes'], 115)
        self.assertEqual(report['native']['relocation_sites'], 3)
        self.assertEqual(report['three_native_bases'], list(BASES))
        self.assertFalse(report['native_gameplay_verified'])
        self.assertFalse(report['gate8_complete'])

    def test_original_runtime_relocated_companion_routines(self):
        if self.tape is None:
            self.skipTest('original vendor tape absent')
        report = verify_selected_runtimes(self.tape, self.rom, [2])
        self.assertEqual(report['selected_routines'], [2, 12, 13])
        self.assertEqual(report['native']['image_bytes'], 24)
        self.assertEqual(report['native']['relocation_sites'], 2)

    def test_next_routine_relative_target_native_link(self):
        if self.tape is None:
            self.skipTest('original vendor tape absent')
        report = verify_selected_runtimes(self.tape, self.rom, [72, 102])
        self.assertIn(72, report['selected_routines'])
        self.assertEqual(report['native']['image_bytes'], 49)

    def test_previous_routine_relative_target_native_link(self):
        if self.tape is None:
            self.skipTest('original vendor tape absent')
        report = verify_selected_runtimes(self.tape, self.rom, [29, 88])
        self.assertEqual(report['selected_routines'], [29, 88])
        self.assertEqual(report['native']['image_bytes'], 67)

    def test_all_original_routines_have_native_source_layout(self):
        if self.tape is None:
            self.skipTest('original vendor tape absent')
        from gate8_original_runtime_types import BASES, N_ROUTINES, OriginalEmitter
        code = compiler_image(self.tape)
        linked, unresolved, empty = set(), set(), 0
        for routine in range(1, N_ROUTINES + 1):
            if OriginalEmitter(code, self.rom, BASES[0]).run(routine) is None:
                empty += 1
                continue
            try:
                result = verify_selected_runtimes(self.tape, self.rom, [routine])
                self.assertIn(routine, result['selected_routines'])
                linked.add(routine)
            except RuntimeLayoutError:
                unresolved.add(routine)
        self.assertEqual(empty, 10)
        self.assertEqual(len(linked), 119)
        self.assertEqual(unresolved, {72, 88})
        self.assertIn(72, verify_selected_runtimes(
            self.tape, self.rom, [72, 102])['selected_routines'])
        self.assertIn(88, verify_selected_runtimes(
            self.tape, self.rom, [29, 88])['selected_routines'])

    def test_root_without_necessary_companion_rejected(self):
        if self.tape is None:
            self.skipTest('original vendor tape absent')
        with self.assertRaisesRegex(RuntimeLayoutError, 'relative jump out of range'):
            verify_selected_runtimes(self.tape, self.rom, [72])
        with self.assertRaisesRegex(RuntimeLayoutError, 'relative jump out of range'):
            verify_selected_runtimes(self.tape, self.rom, [88])


if __name__ == '__main__':
    unittest.main()

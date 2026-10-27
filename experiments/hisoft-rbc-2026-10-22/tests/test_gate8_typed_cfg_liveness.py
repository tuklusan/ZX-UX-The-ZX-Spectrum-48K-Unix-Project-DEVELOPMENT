"""Typed whole-Z80 CFG and conservative register liveness checks."""
from pathlib import Path
import sys
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from gate8_typed_cfg_liveness import inspect_typed_cfg_liveness, TypedCFGError


class TypedWholeCFGTests(unittest.TestCase):
    def test_reachable_internal_branch_and_unreachable_instruction(self):
        source = ('section text\nglobal start\nstart:\n'
                  '    ld a,1\n    jp done\n    nop\n'
                  'done:\n    ld a,2\n    ret\n')
        report = inspect_typed_cfg_liveness(source)
        self.assertEqual(report['instruction_count'], 5)
        self.assertEqual(report['reachable_instructions'], 4)
        self.assertEqual(report['unreached_instructions'], 1)
        self.assertEqual(report['unresolved_control_edges'], 0)
        self.assertTrue(report['source_liveness_converged'])
        self.assertFalse(report['rewrite_safe_to_admit'])

    def test_opaque_indirect_and_protected_data_do_not_become_edges(self):
        source = ('section text\nglobal start\nstart:\n'
                  '    jp (hl)\n    db 195,0,118,255\n'
                  'entry:\n    call datum\n    ret\n'
                  'section data\ndatum:\n    dw entry\n')
        report = inspect_typed_cfg_liveness(source)
        self.assertGreater(report['unresolved_control_edges'], 0)
        self.assertEqual(report['reachable_instructions'], 1)
        self.assertGreater(report['register_effects_unknown'], 0)
        self.assertFalse(report['native_behavior_verified'])

    def test_no_labels_for_opaque_bytes_or_unknown_entry(self):
        for source in (
                'section text\nstart:\n db 0\n',
                'section text\nstart:\n nop\nstart:\n ret\n',
                'section text\nstart:\n nop\nsection data\n ret\n'):
            with self.subTest(source=source):
                with self.assertRaises(TypedCFGError):
                    inspect_typed_cfg_liveness(source)

    def test_backward_register_liveness_is_conservative(self):
        source = ('section text\nstart:\n'
                  '    ld a,2\n    ld a,3\n    ret\n')
        report = inspect_typed_cfg_liveness(source)
        self.assertEqual(report['register_effects_modelled'], 2)
        self.assertFalse(report['rewrite_safe_to_admit'])


if __name__ == '__main__':
    unittest.main()

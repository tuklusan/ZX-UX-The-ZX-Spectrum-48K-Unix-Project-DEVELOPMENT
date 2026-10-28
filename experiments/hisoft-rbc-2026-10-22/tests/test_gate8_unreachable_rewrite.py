"""Only inaccessible whole-source instructions may be removed without clock changes."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from gate8_unreachable_rewrite import (check_unreachable_deletions,
                                        UnreachableRewriteError)


class ClosedCFG(unittest.TestCase):
    def setUp(self):
        self.original = ('    section text\n    global start\nstart:\n'
                         '    jp done\ndead:\n    ld a,a\n    ld b,b\n'
                         'done:\n    ret\n')
        self.optimized = self.original.replace('    ld a,a\n    ld b,b\n', '')

    def test_dead_register_operations_can_be_dropped_without_execution(self):
        report = check_unreachable_deletions(self.original, self.optimized)
        self.assertEqual(report['deleted_unreachable_instructions'], 2)
        self.assertEqual(report['reachable_source_instructions'], 2)
        for source in (self.original, self.optimized):
            obj = ras.assemble_text(source, 'closed-graph.s')
            linked = rld.link([rld.Obj(obj, 'closed-graph.sso')], [],
                              entry='start', stack=384)[0]
            self.assertTrue(rld.parse_ssx(linked)['image'])

    def test_real_upstream_dead_code_relink_and_probe_equivalence(self):
        try:
            from upeepz80 import PeepholeOptimizer
        except ImportError:
            self.skipTest('requires verified upstream optimizer')
        from gate8_native_whole_optimizer import verify_whole_optimizer_candidate
        obj = ras.assemble_text(self.original, 'closed-native-original.s')
        native = rld.link([rld.Obj(obj, 'closed-native-original.sso')], [],
                          entry='start', stack=384)[0]
        result = verify_whole_optimizer_candidate(
            self.original, native, PeepholeOptimizer().optimize,
            native_probe=True)
        self.assertEqual(result['closed_cfg_dead_code_proof']
                         ['deleted_unreachable_instructions'], 2)
        self.assertEqual(result['candidate_file_bytes_saved'], 2)
        self.assertTrue(result['bounded_native_execution']['bounded_exit_states_match'])
        self.assertFalse(result['optimizer_candidate_admitted_for_publication'])
        self.assertFalse(result['native_behavior_verified'])
        self.assertFalse(result['full_program_optimized'])

    def test_source_data_and_bss_are_preserved_after_native_relink(self):
        try:
            from upeepz80 import PeepholeOptimizer
        except ImportError:
            self.skipTest('requires verified upstream optimizer')
        from gate8_native_whole_optimizer import verify_whole_optimizer_candidate
        code = (self.original + '    section data\nasset:\n    db 195,0,118,255\n'
                '    section bss\n    ds 7\n')
        obj = ras.assemble_text(code, 'closed-data.s')
        before = rld.link([rld.Obj(obj, 'closed-data.sso')], [],
                          entry='start', stack=384)[0]
        checked = verify_whole_optimizer_candidate(
            code, before, PeepholeOptimizer().optimize,
            expected_runtime_bytes=bytes((195, 0, 118, 255)))
        self.assertEqual(checked['candidate_file_bytes_saved'], 2)
        self.assertEqual(checked['candidate_total_bytes_saved'], 2)
        self.assertTrue(checked['protected_source_lines_preserved'])
        self.assertFalse(checked['optimizer_candidate_admitted_for_publication'])

    def test_reachable_instruction_deletion_is_rejected(self):
        with self.assertRaisesRegex(UnreachableRewriteError, 'entry or resource'):
            check_unreachable_deletions(self.original,
                                        self.original.replace('    jp done\n', ''))

    def test_unknown_external_entries_and_symbolic_data_are_rejected(self):
        with self.assertRaises(UnreachableRewriteError):
            check_unreachable_deletions(self.original.replace('global start',
                'global start,dead'), self.optimized)
        with self.assertRaises(UnreachableRewriteError):
            check_unreachable_deletions(self.original + '    section data\n    dw dead\n',
                                        self.optimized + '    section data\n    dw dead\n')

    def test_source_sections_must_not_rewind(self):
        original = (self.original + '    section data\n    db 1\n'
                    '    section text\n    nop\n')
        with self.assertRaisesRegex(UnreachableRewriteError, 'section repeats'):
            check_unreachable_deletions(original, self.optimized)

    def test_branch_into_deleted_instruction_is_rejected(self):
        original = self.original.replace('jp done', 'jp dead')
        candidate = self.optimized.replace('jp done', 'jp dead')
        with self.assertRaisesRegex(UnreachableRewriteError, 'entry or resource'):
            check_unreachable_deletions(original, candidate)

    def test_unmodelled_rom_or_stack_effects_cannot_enter_proof(self):
        for text in (self.original.replace('jp done', 'call done'),
                     self.original.replace('ld a,a', 'push af'),
                     self.original.replace('ld a,a', 'ld a,(23692)'),
                     self.original.replace('jp done', 'jp (hl)')):
            with self.subTest(text=text):
                with self.assertRaisesRegex(UnreachableRewriteError, 'unmodelled'):
                    check_unreachable_deletions(text, self.optimized)

    def test_inserting_new_code_cannot_pass_as_dead_deletion(self):
        with self.assertRaisesRegex(UnreachableRewriteError, 'source-only'):
            check_unreachable_deletions(self.original, self.optimized.replace(
                '    ret\n', '    inc a\n    ret\n'))


if __name__ == '__main__':
    unittest.main()

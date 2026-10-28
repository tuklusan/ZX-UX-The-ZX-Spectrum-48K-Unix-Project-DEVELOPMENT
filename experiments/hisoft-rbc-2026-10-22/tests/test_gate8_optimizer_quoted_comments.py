"""Full-source optimizer protects quoted DB bytes and AF shadow registers."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from gate8_native_whole_optimizer import (
    _control_transfers, _observable_accesses, _state_context,
    WholeOptimizerError, verify_whole_optimizer_candidate)

SOURCE = (
    '    section text\n    global start\nstart:\n'
    '    ld hl, message\n'
    "    ex af,af' ; quote in comment: \"\n"
    '    jp exit\n'
    'message:\n'
    '    db "Before;After",39 ; quote in comment: \"\n'
    'exit:\n'
    '    ret\n'
    '    section data\n'
    '    db "Next;Value", 0 ; annotation\n'
    '    section bss\n    ds 2\n')


def native_link(assembly):
    obj = ras.assemble_text(assembly, 'rbc-g8-source-comment.s')
    return rld.link([rld.Obj(obj, 'rbc-g8-source-comment.sso')], [],
                    entry='start', stack=384)[0]


class QuotedResourceOptimizerTests(unittest.TestCase):
    def test_source_classifier_handles_quoted_semicolon_and_shadow_register(self):
        self.assertIn(('start', 'ex', "af,af'"), _observable_accesses(SOURCE))
        self.assertEqual(_control_transfers(SOURCE),
                         (('start', 'jp', 'exit'), ('exit', 'ret', '')))
        self.assertIn(('message', 'db', '"Before;After",39'),
                      _state_context(SOURCE))
        self.assertIn(('start', 'ex', "af,af'"), _state_context(SOURCE))

    def test_comment_only_change_relinks_byte_identical_at_three_bases(self):
        candidate = SOURCE.replace(' ; quote in comment: "', '')
        candidate = candidate.replace(' ; annotation\n', '\n')
        before = native_link(SOURCE)
        after = native_link(candidate)
        self.assertEqual(before, after)
        report = verify_whole_optimizer_candidate(
            SOURCE, before, lambda _text: candidate)
        self.assertTrue(report['native_candidate_link_verified'])
        self.assertTrue(report['candidate_byte_identical'])
        self.assertFalse(report['optimizer_candidate_admitted_for_publication'])
        original = rld.parse_ssx(before)
        adjusted = rld.parse_ssx(after)
        for base in (0x6000, 0x7000, 0x8000):
            with self.subTest(base=base):
                self.assertEqual(
                    rld.relocate(original['image'], original['relocs'], base),
                    rld.relocate(adjusted['image'], adjusted['relocs'], base))

    def test_data_change_cannot_be_hidden_after_quote(self):
        replaced = SOURCE.replace('Before;After', 'Before;other')
        with self.assertRaisesRegex(WholeOptimizerError, 'protected'):
            verify_whole_optimizer_candidate(SOURCE, native_link(SOURCE),
                                             lambda _: replaced)


if __name__ == '__main__':
    unittest.main()

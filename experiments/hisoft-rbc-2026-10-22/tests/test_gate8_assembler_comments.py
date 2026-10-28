"""Assembler comments never own resource bytes or executable labels."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from symbolic_z80 import (_canonical_source_line, _check_protected,
                          _check_optimizer_output, SymbolicError)
from gate8_native_whole_optimizer import verify_whole_optimizer_candidate

SOURCE = ('    section text\n    global start\nstart:\n'
          '    ld hl,data_label ; ordinary register comment\n'
          '    ret ; an unclosed quote in a comment: "\n'
          '    section data\ndata_label:\n'
          '    db "Ab;Cd",69 ; original resource annotation\n'
          '    dw start ; reference to executable text\n')


def link(text):
    obj = ras.assemble_text(text, 'gate8-comment-resource.s')
    return rld.link([rld.Obj(obj, 'gate8-comment-resource.sso')], [],
                    entry='start', stack=384)[0]


class AssemblerCommentResourceTests(unittest.TestCase):
    def test_comment_changes_do_not_mutate_protected_source_or_native_bytes(self):
        candidate = SOURCE.replace(' ; ordinary register comment', '')
        candidate = candidate.replace(' ; an unclosed quote in a comment: "', '')
        candidate = candidate.replace(' ; original resource annotation',
                                      ' ; unrelated comment with a \' quote')
        candidate = candidate.replace(' ; reference to executable text', '')
        self.assertEqual(
            _canonical_source_line('DB "Ab;Cd",69 ; \' unfinished comment',
                                   strip_comment=True),
            'db "Ab;Cd",69')
        _check_protected(SOURCE, candidate, {'start'})
        _check_optimizer_output(candidate)
        original_ssx, candidate_ssx = link(SOURCE), link(candidate)
        self.assertEqual(original_ssx, candidate_ssx)
        report = verify_whole_optimizer_candidate(
            SOURCE, original_ssx, lambda _text: candidate)
        self.assertTrue(report['native_baseline_source_reassembled'])
        self.assertTrue(report['candidate_byte_identical'])
        self.assertFalse(report['optimizer_candidate_admitted_for_publication'])
        info = rld.parse_ssx(original_ssx)
        self.assertIn(b'Ab;CdE', info['image'])
        for base in (0x6000, 0x7000, 0x8000):
            with self.subTest(base=base):
                self.assertEqual(
                    rld.relocate(rld.parse_ssx(candidate_ssx)['image'],
                                 info['relocs'], base),
                    rld.relocate(info['image'], info['relocs'], base))

    def test_only_comments_may_change(self):
        for modified in (
                SOURCE.replace('Ab;Cd', 'Ab;cd'),
                SOURCE.replace('dw start', 'dw data_label'),
                SOURCE.replace('data_label:', 'renamed:'),
                SOURCE.replace('db "Ab;Cd",69', 'db "Ab;Cd",70'),
        ):
            with self.subTest(modified=modified):
                with self.assertRaisesRegex(SymbolicError,
                                            'changed protected data'):
                    _check_protected(SOURCE, modified, {'start'})

    def test_incomplete_literal_outside_comment_is_rejected(self):
        with self.assertRaisesRegex(SymbolicError, 'unterminated quoted'):
            _check_optimizer_output(
                'section text\nstart:\n db "unfinished;literal\n')


if __name__ == '__main__':
    unittest.main()

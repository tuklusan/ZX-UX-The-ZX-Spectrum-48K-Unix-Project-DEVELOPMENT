"""The optimizer may not silently change case-sensitive Z80 data strings."""
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
from gate8_native_whole_optimizer import (verify_whole_optimizer_candidate,
                                         WholeOptimizerError)


ORIGINAL = ('    section text\n    global start\nstart:\n'
            '    ret\n    section data\n'
            'message:\n    db "Ab;Cd",69 ; protected bytes\n')


def native(source):
    obj = ras.assemble_text(source, 'quoted-resource.s')
    return rld.link([rld.Obj(obj, 'quoted-resource.sso')], [],
                    entry='start', stack=384)[0]


class QuotedResourceProtectionTests(unittest.TestCase):
    def test_quoted_case_and_semicolon_are_protected_native_bytes(self):
        baseline = native(ORIGINAL)
        info = rld.parse_ssx(baseline)
        self.assertEqual(info['image'], b'\xc9Ab;CdE')
        for before, after in (('Ab;Cd', 'ab;Cd'), ('Ab;Cd', 'Ab;cd'),
                              ('Ab;Cd', 'Ab;CD')):
            candidate = ORIGINAL.replace(before, after)
            with self.subTest(after=after):
                self.assertNotEqual(native(candidate), baseline)
                with self.assertRaisesRegex(SymbolicError,
                                            'changed protected data'):
                    _check_protected(ORIGINAL, candidate, {'start'})
                # An optimizer may return linked Z80, but these resources
                # were not typed as executable code to be optimized.
                with self.assertRaisesRegex(WholeOptimizerError,
                                            'protected data'):
                    verify_whole_optimizer_candidate(
                        ORIGINAL, baseline, lambda _: candidate)
        for base in (0x6000, 0x7000, 0x8000):
            with self.subTest(base=base):
                self.assertEqual(rld.relocate(info['image'], info['relocs'],
                                              base), info['image'])

    def test_assembler_syntax_case_only_remains_harmless(self):
        source = ORIGINAL.replace('    db "Ab;Cd",69',
                                  '    DB "Ab;Cd",69')
        self.assertEqual(native(source), native(ORIGINAL))
        _check_protected(ORIGINAL, source, {'start'})
        _check_optimizer_output(source)

    def test_semicolon_within_quoted_data_is_never_a_source_comment(self):
        self.assertEqual(
            _canonical_source_line('    DB "Ab;Cd",69 ; comment',
                                   strip_comment=True),
            'db "Ab;Cd",69')
        self.assertEqual(
            _canonical_source_line('    DB \'A;B\',66',
                                   strip_comment=True),
            "db 'A;B',66")
        with self.assertRaisesRegex(SymbolicError,
                                    'unterminated quoted'):
            _check_optimizer_output('section text\n    db "unfinished;bytes\n')


if __name__ == '__main__':
    unittest.main()

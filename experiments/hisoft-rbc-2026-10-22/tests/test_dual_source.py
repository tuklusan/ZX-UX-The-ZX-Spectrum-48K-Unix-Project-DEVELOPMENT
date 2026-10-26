"""BAS/TZX fidelity: only ROM-irrelevant formatting may be ignored."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from dual_source import SemanticDifference, LosslessConversionError, validated_lines, semantic_check


def pack(rows):
    return b''.join(bytes((n >> 8, n & 255, len(b) & 255, len(b) >> 8)) + b
                    for n, b in rows)


T = {0xF5: 'PRINT', 0xCB: 'THEN', 0xFA: 'IF', 0xEB: 'FOR', 0xCC: 'TO'}


class Fidelity(unittest.TestCase):
    def compare(self, a, b):
        return semantic_check(pack([(10, a)]), pack([(10, b)]), validated_lines, T, 'BAS/TZX')

    def test_identical_and_keyword_only_spaces(self):
        self.compare(b'\xf5"abc"\r', b'\xf5 "abc"\r')

    def test_literal_spelling_is_not_repaired(self):
        with self.assertRaisesRegex(SemanticDifference, 'Line 10'):
            self.compare(b'\xebI=1TO10\r', b'\xebI=1\xcc10\r')

    def test_remark_bytes_are_preserved_for_equivalence(self):
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xf5"A B"\r', b'\xf5"AB"\r')
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xea A B\r', b'\xea A  B\r')
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xf51: \xea note\r', b'\xf51\r')
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xf51: \xea note\r', b'\xf51: \xea changed\r')
        # The spelling REM inside a string is still executable data.
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xf5"REM A"\r', b'\xf5"REM B"\r')
        # Actual statements preceding a REM remain significant.
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xf51:\xea note\r', b'\xf52:\xea note\r')

    def test_only_rem_edge_spaces_may_differ(self):
        self.compare(b'\xea  NOTE  HERE   \r', b'\xeaNOTE  HERE\r')
        with self.assertRaisesRegex(SemanticDifference, 'Line 10'):
            self.compare(b'\xeaNOTE  HERE\r', b'\xeaNOTE HERE\r')
        with self.assertRaisesRegex(SemanticDifference, 'Line 10'):
            self.compare(b'\xeaNOTE\x7f\r', b'\xeaNOTE\x7e\r')

    def test_print_separator_whitespace_outside_quote(self):
        self.compare(b'\xf5"A " ;X$\r', b'\xf5"A ";X$\r')
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xf5"A " ;X$\r', b'\xf5"A";X$\r')

    def test_number_cache_spacing_before_to_token(self):
        cache = b'\x0e\x00\x00\x14\x00\x00'
        self.compare(b'\xebI=20 '+cache+b'\xcc30\r',
                     b'\xebI=20'+cache+b' \xcc30\r')
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xebI=20 '+cache+b'\xcc30\r',
                         b'\xebI=21'+cache+b' \xcc30\r')
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xebI=20 '+cache+b'\xcc30\r',
                         b'\xebI=20'+cache+b' TO 30\r')

    def test_regenerated_numeric_cache_is_not_source(self):
        self.compare(b'\xf510\x0e\x00\x00\x0a\x00\x00\r',
                     b'\xf510\x0e\x00\x00\x0a\x00\x00\r')
        self.compare(b'\xf510\x0e\x00\x00\x0a\x00\x00\r',
                     b'\xf510\x0e\x01\x00\x00\x00\x00\r')
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xf510\r', b'\xf511\r')

    def test_all_original_tzx_listings_match_authoritative_bas_bytes(self):
        from pathlib import Path
        import importlib.util
        root = Path(__file__).resolve().parents[3]
        tool = root / 'build/tools/zx-tzx2bas.py'
        spec = importlib.util.spec_from_file_location('zx_tzx2bas_audit', tool)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        games = root / 'src/bonus/60-programs'
        if not games.is_dir():
            self.skipTest('original BAS/TZX corpus unavailable')
        checked = 0
        for folder in sorted(games.iterdir()):
            if not folder.is_dir() or not folder.name[:2].isdigit():
                continue
            with self.subTest(game=folder.name):
                tape = (folder / 'BASIC' / (folder.name + '.tzx')).read_bytes()
                bas = (folder / 'BASIC' / (folder.name + '.bas')).read_bytes()
                self.assertEqual(module.listing(tape).encode('ascii'), bas)
                checked += 1
        self.assertEqual(checked, 60)

    def test_tzx_exports_pass_strict_rbc_reader_without_repair(self):
        """The converter supplies syntactically tokenizable source, not a waiver.

        Tape-byte/authoritative-BAS divergences still fail independent
        fidelity checks; unsupported USR/POKE restrictions stay downstream.
        """
        import importlib.util
        from basic_listing import encode_strict_listing
        root = Path(__file__).resolve().parents[3]
        tool = root / 'build/tools/zx-tzx2bas.py'
        spec = importlib.util.spec_from_file_location('zx_tzx2bas_reader', tool)
        converter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(converter)
        collection = root / 'src/bonus/60-programs'
        if not collection.is_dir():
            self.skipTest('preserved BAS/TZX corpus unavailable')
        passed = rejected = 0
        affected = {}
        for game in sorted(collection.iterdir()):
            if not game.is_dir() or not game.name[:2].isdigit():
                continue
            with self.subTest(game=game.name):
                original = game / 'BASIC' / (game.name + '.bas')
                tape = game / 'BASIC' / (game.name + '.tzx')
                text = converter.listing(tape.read_bytes())
                assert text.isascii()
                tokens = encode_strict_listing(text)
                self.assertEqual(tokens, encode_strict_listing(original.read_text('ascii')))
                self.assertEqual(text.encode('ascii'), original.read_bytes())
                program = list(converter.basic_programs(tape.read_bytes()))[0][1]
                try:
                    semantic_check(program, tokens, None,
                                   converter.rom_keywords(), 'TZX conversion')
                    passed += 1
                except SemanticDifference as exc:
                    rejected += 1
                    affected[game.name] = str(exc)
        self.assertEqual((passed, rejected), (60, 0))
        self.assertEqual(affected, {})
        self.assertTrue(all('Line ' in reason for reason in affected.values()))

    def test_rejects_bad_line_structure(self):
        with self.assertRaisesRegex(LosslessConversionError, 'non-increasing'):
            validated_lines(pack([(10, b'\xf5\r'), (10, b'\xf5\r')]))
        with self.assertRaisesRegex(LosslessConversionError, 'end-of-line'):
            validated_lines(pack([(10, b'\xf5')]))


if __name__ == '__main__':
    unittest.main()

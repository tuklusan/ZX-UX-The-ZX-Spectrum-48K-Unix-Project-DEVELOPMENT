"""The RBC compiler keeps HiSoft codegen, original ROM syntax and one input path."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
RBC = ROOT / 'build/tmp/rbc-round2/current/rbc/rbc.py'


class ThinWrapper(unittest.TestCase):
    def prepared(self):
        self.assertTrue(RBC.is_file(), 'RBC checkpoint must be prepared before tests')
        return RBC.read_text()

    def test_direct_hisoft_codegen(self):
        text = self.prepared()
        self.assertIn('compiler.Compiler(img,rom,ramtop=top)', text)
        self.assertIn('res=c.compile_whole(program)', text)
        self.assertNotIn('compiler_with_computed_lines', text)

    def test_no_source_level_semantics_rewrites(self):
        text = self.prepared()
        start = text.index('program = source.tokenize_directives(program,kw)')
        end = text.index('checks = analyze_lines(', start)
        statements = text[start:end]
        self.assertNotIn('program, ', statements)
        self.assertNotIn('resolve_missing_targets', text)
        self.assertNotIn('remove_duplicate_for', text)

    def test_no_language_control_flow_patch(self):
        text = self.prepared()
        for marker in ('install_for_restart', 'install_native_run',
                       'install_dynamic_string_width', 'install_native_loops',
                       'ProcessLoopStack', 'compiler_with_computed_lines'):
            self.assertNotIn(marker, text)

    def test_hisoft_controls_for_next(self):
        text = self.prepared()
        self.assertIn('res=c.compile_whole(program)', text)
        for forbidden in ('install_for_restart', 'remove_duplicate_for',
                          'ProcessLoopStack', 'install_native_loops'):
            self.assertNotIn(forbidden, text)
        for obsolete in ('for_restart.py', 'duplicate_for.py'):
            self.assertFalse((STAGE / obsolete).exists())

    def test_only_zxux_specific_runtime_shims(self):
        text = self.prepared()
        for required in ('install_native_pause(compiler)',
                         'install_native_keyread(compiler)',
                         'install_native_sysvars(compiler)'):
            self.assertIn(required, text)
        self.assertIn('enforce_numeric_usr(', text)
        self.assertIn('validate_rom_lines(program, rom)', text)
        self.assertIn('memory_required(rld.parse_ssx(ssx)', text)

    def test_upstream_tokenizer_is_exclusive(self):
        text = self.prepared()
        self.assertIn("src.read_text(encoding='ascii')", text)
        self.assertIn('program = encode_strict_listing(listing)', text)
        self.assertIn('return src.stem[:10], program', text)
        self.assertNotIn('source.tokenize_line(', text)
        self.assertNotIn('source.hide_numbers(', text)
        self.assertNotIn("encoding='latin-1'", text)
        self.assertIn('return compiler, hbcimage, source', text)


if __name__ == '__main__':
    unittest.main()

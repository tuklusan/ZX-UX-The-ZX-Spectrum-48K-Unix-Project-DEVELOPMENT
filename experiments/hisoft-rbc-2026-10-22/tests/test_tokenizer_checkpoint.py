"""The prepared executable contains no legacy input lexer or number writer."""
from pathlib import Path
import unittest
import sys

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
RBC = ROOT / 'build/tmp/rbc-round2/current/rbc/rbc.py'


class UpstreamRBC(unittest.TestCase):
    def test_upstream_revision(self):
        sys.path.insert(0, str(STAGE))
        from basic_listing import UPSTREAM_REVISION
        self.assertEqual(UPSTREAM_REVISION, '0ddb25e4c38ce4ccb5a43e85fb57e683bd274f59')
        self.assertTrue((STAGE / 'bas2tap.py').is_file())
        self.assertTrue((STAGE / 'bas2tap_syntax.py').is_file())

    def test_compiler_uses_new_source_adapter_only(self):
        self.assertTrue(RBC.is_file(), 'prepare the compiler checkpoint first')
        source = RBC.read_text()
        self.assertIn('program = encode_strict_listing(listing)', source)
        self.assertIn('validate_rom_lines(program, rom)', source)
        self.assertNotIn('source.tokenize_line(', source)
        self.assertNotIn('source.hide_numbers(', source)
        self.assertNotIn("src.read_text(encoding='latin-1')", source)
        self.assertIn('res=c.compile_whole(program)', source)

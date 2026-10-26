"""Only independently harmless whitespace can differ between tape and ASCII."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'stage'))
from dual_source import semantic_check, SemanticDifference


def packed(body):
    return b'\x00\x0a' + len(body).to_bytes(2,'little') + body


class TapeWhitespaceFidelity(unittest.TestCase):
    def compare(self,a,b):
        return semantic_check(packed(a),packed(b),None,{0xf5:'PRINT',0xea:'REM'},'TZX')

    def test_spaces_before_statement_token_have_no_effect(self):
        self.compare(b' \xf5"HI"\r',b'\xf5"HI"\r')

    def test_blank_line_stays_blank_at_same_line_number(self):
        self.compare(b' \r',b'\r')

    def test_remark_only_ignores_edge_spaces(self):
        self.compare(b'\xea  A\r', b'\xea A\r')
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xea A  B\r', b'\xea A B\r')

    def test_spaces_in_strings_are_not_ignored(self):
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xf5"A  B"\r',b'\xf5"A B"\r')

    def test_keyword_not_reconstructed(self):
        with self.assertRaises(SemanticDifference):
            self.compare(b'\xf5"X"\r',b'PRINT"X"\r')

if __name__=='__main__':unittest.main()
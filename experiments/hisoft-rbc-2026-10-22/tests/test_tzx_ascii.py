"""A tokenized tape must retain every source byte through its ASCII adapter."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'stage'))
from tzx_ascii import LosslessConversionError, to_ascii_listing, confirm_roundtrip

TOKENS={0xF5:'PRINT',0xEA:'REM',0xED:'GO SUB',0xCB:'THEN',0xFA:'IF',0xEB:'FOR',0xCC:'TO'}

class TapeAsciiTests(unittest.TestCase):
    def test_literal_number_bytes_and_keyword_boundaries(self):
        src=b'\xfa 1\x0e\0\0\1\0\0\xcb\xf5 "OK"\r'
        result=to_ascii_listing([(10,src)],TOKENS)
        self.assertIn('IF {20}',result)
        self.assertIn('{0E}{00}{00}{01}{00}{00}',result)
        self.assertIn('THEN PRINT ',result)

    def test_remark_preserves_spaces_and_literal_keyword_byte(self):
        src=b'\xea     PAYPACKETS                          BY  \xf5\r'
        result=to_ascii_listing([(10,src)],TOKENS)
        self.assertIn('REM '+'{20}'*5+'{50}{41}{59}',result)
        self.assertIn('{F5}',result)
        self.assertEqual(result.count('{20}'),33)

    def test_quote_and_semicolon_survive(self):
        result=to_ascii_listing([(10,b'\xf5"{90} \xf5";2\x0e\0\0\2\0\0\r')],TOKENS)
        self.assertIn('PRINT "',result)
        self.assertIn('{7B}{39}{30}{7D}{20}{F5}"',result)
        self.assertIn('{3B}{32}{0E}',result)

    def test_spaces_before_keyword_preserved(self):
        result=to_ascii_listing([(10,b'\xebF=20 \x0e\0\0\x14\0\0\xcc30\r')],TOKENS)
        self.assertIn('{32}{30}{20}{0E}',result)
        self.assertIn('TO {33}{30}',result)

    def test_identical_program_is_accepted(self):
        confirm_roundtrip(b'abc',b'abc',lambda _: [])

    def test_changed_hidden_bytes_report_line(self):
        with self.assertRaisesRegex(LosslessConversionError,'Line 10: token round-trip'):
            confirm_roundtrip(b'abc',b'abd',lambda x:[(10,b'1\x0e'+(b'12345' if x==b'abc' else b'12346'))])

    def test_rejects_bad_line_structure(self):
        with self.assertRaisesRegex(LosslessConversionError,'numeric cache'):
            to_ascii_listing([(10,b'\xf5 1\x0e\1\r')],TOKENS)
        with self.assertRaisesRegex(LosslessConversionError,'number'):
            to_ascii_listing([(10000,b'\xf5 1\r')],TOKENS)

if __name__=='__main__': unittest.main()
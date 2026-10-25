import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, main

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from safety_usr import UnsupportedUsr, allow_typed_usr_findings, enforce_numeric_usr

TOK = {0xc0: 'USR', 0xf4: 'POKE', 0xea: 'REM', 0xf5: 'PRINT',
       0xc2: 'CHR$', 0xb0: 'VAL', 0xb1:'VAL$', 0xf1:'LET'}

def tok(s):
    for name, value in sorted([(v, k) for k, v in TOK.items()], key=lambda t:-len(t[0])):
        s=s.replace('{'+name+'}', chr(value))
    return s.encode('latin1')

class TypedUsrGate(TestCase):
    def gate(self, value):
        b=tok(value)
        count=b.count(bytes([0xc0]))
        findings=[SimpleNamespace(line=10, operation='USR',severity='block',classification='raw_machine_code_address') for _ in range(count)]
        allow_typed_usr_findings([(10,b)], findings, TOK)
        enforce_numeric_usr([(10,b)], findings, [], TOK)
        self.assertTrue(all(f.severity=='info' and f.classification=='requires_compiler_string_type' for f in findings))

    def test_literal_string_outside_poke(self):
        self.gate('{LET} X={USR} "a"')
    def test_string_variable_outside_poke(self):
        self.gate('{LET} X={USR} A$')
    def test_chr_expression(self):
        self.gate('{POKE} {USR} {CHR$}(143+M)+L,12')
    def test_val_string_return(self):
        self.gate('{LET} X={USR} {VAL$} A$')
    def test_quoted_text_and_rem(self):
        allow_typed_usr_findings([(10,tok('{PRINT} "USR":{REM} {USR} 32768'))], [], TOK)
        enforce_numeric_usr([(10,tok('{PRINT} "USR":{REM} {USR} 32768'))], [], [], TOK)
    def test_numeric_direct_is_rejected(self):
        for s in ('{LET} X={USR} 32768','{LET} X={USR} {VAL} A$',
                  '{LET} X={USR} ({VAL} A$)', '{LET} X={USR} ({USR} "a")',
                  '{POKE} {USR} 20000,0'):
            with self.subTest(s=s), self.assertRaises(UnsupportedUsr):
                self.gate(s)
    def test_review_count_is_fail_closed(self):
        with self.assertRaises(UnsupportedUsr):
            allow_typed_usr_findings([(10,tok('{LET} X={USR} A$'))], [], TOK)
    def test_other_line_review_is_rejected(self):
        f=[SimpleNamespace(line=11,operation='USR',severity='block',classification='x')]
        with self.assertRaises(UnsupportedUsr):
            allow_typed_usr_findings([(10,tok('{USR} A$'))], f, TOK)

if __name__=='__main__':main()

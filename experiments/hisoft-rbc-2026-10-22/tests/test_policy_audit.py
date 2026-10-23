#!/usr/bin/env python3
"""Focused tests for the read-only BASIC safety survey."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"stage"))
import audit_policy as policy

class PolicySurveyTests(unittest.TestCase):
    def test_numeric_usr_any_expression(self):
        s='10 PRINT USR 32768:LET A=USR (33000):IF USR 100=1 THEN PRINT 1'
        x=policy.audit_lines(policy.from_text((s+'\n').encode()),'text')
        self.assertEqual([i['status'] for i in x],['numeric_usr']*3)

    def test_quote_comment_data(self):
        src=b'10 PRINT "USR 123, POKE 50,9":REM USR 34\n20 DATA USR 12,POKE 10,11:PRINT USR "a"\n'
        x=policy.audit_lines(policy.from_text(src),'text')
        self.assertEqual([(i['line'],i['operation'],i['status']) for i in x],[(20,'USR','literal_graphics_character')])

    def test_string_usr_and_expression_types(self):
        s=b'10 LET X=USR "a"+USR CHR$ (144+I)+USR A$\n'
        x=policy.audit_lines(policy.from_text(s),'text')
        self.assertEqual([i['status'] for i in x],['literal_graphics_character','string_expression_requires_type_and_range_proof','string_variable_requires_length_proof'])

    def test_poke_literal_and_unknown(self):
        s=b'30 POKE (23000+58),1:POKE (50000+K)*2,VAL X$\n'
        x=policy.audit_lines(policy.from_text(s),'text')
        self.assertEqual([(i['operation'],i['status']) for i in x], [('POKE','constant_proved_needs_memory_policy'),('POKE','needs_exact_control_flow_proof'),('VAL','runtime_string_expression_needs_safe_evaluator')])
        self.assertEqual(x[0]['address'],23058)

    def test_tzx_tokenized_operator_and_quoted(self):
        code=bytes([0xF5,32,34,0xc0,34,58,0xF1,32,65,61,0xC0,32,51,50,56,48,13])
        x=policy.audit_lines([(200,code)],'tape')
        self.assertEqual([(i['operation'],i['status']) for i in x],[('USR','numeric_usr')])

if __name__=='__main__':unittest.main()

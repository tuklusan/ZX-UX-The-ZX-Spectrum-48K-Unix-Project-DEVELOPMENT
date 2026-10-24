"""VAL must not be a route around the numeric USR ban."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from val_guard import UnsafeVal,guard_val


def verify(*rows):
    return guard_val([(i+10,body.encode('latin1')) for i,body in enumerate(rows)],{})


class ValGuardTests(unittest.TestCase):
    def test_numeric_literals(self):
        self.assertEqual(len(verify('PRINT VAL "12"','LET A=VAL " -12.5E-3 "',
                                    'PRINT VAL ("0.125")')),3)

    def test_dynamic_string_is_deferred_to_native_guard(self):
        self.assertTrue(verify('INPUT A$:PRINT VAL A$')[0]['runtime_guard_required'])

    def test_literal_machine_code_is_blocked(self):
        with self.assertRaisesRegex(UnsafeVal,'E_VAL_EXPR'):
            verify('LET X=VAL "USR 32768"')

    def test_literal_concatenation_cannot_bypass_runtime_check(self):
        self.assertEqual(len(verify('LET X=VAL "1"+A$')), 1)

    def test_comments_data_and_quotes_do_not_execute(self):
        self.assertEqual(verify('PRINT "VAL USR 32768"',
                                'DATA VAL "USR 32768":PRINT 10',
                                'PRINT 10:'+chr(234)+' VAL "32768"'),[])

    def test_non_numeric_literal_is_blocked(self):
        with self.assertRaises(UnsafeVal):verify('LET X=VAL "1+USR 32768"')

    def test_val_string_evaluation_is_blocked(self):
        with self.assertRaisesRegex(UnsafeVal,r'VAL\$ runtime'):
            verify('PRINT VAL$ ("STR$ (USR 32768)")')

if __name__=='__main__':unittest.main()

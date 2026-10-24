"""VAL/USR gate must check real native Z80 and strict source handling."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from val_guard import guard_val, UnsafeVal
from test_round2_val_native import ValNativeGuard


def audit(text):
    return guard_val([(10, text.encode('latin1'))], {})


class Round2Val(unittest.TestCase):
    def test_variable_string_numeric_expression_is_allowed(self):
        self.assertTrue(audit('PRINT VAL A$')[0]['runtime_guard_required'])

    def test_input_variable_string_is_allowed(self):
        self.assertTrue(audit('INPUT A$: PRINT VAL A$')[0]['runtime_guard_required'])

    def test_constant_expression_is_allowed(self):
        self.assertEqual(audit('LET X=VAL "2+3*4"')[0]['literal'], '2+3*4')

    def test_nested_expression_is_allowed_in_source(self):
        self.assertEqual(audit('PRINT VAL ("PI/2")')[0]['literal'], 'PI/2')

    def test_dynamic_usr_is_rejected_by_executable_z80(self):
        self.assertEqual(ValNativeGuard().run_guard('USR 32768')[0], 8)

    def test_nested_constructed_usr_stays_blocked(self):
        self.assertEqual(ValNativeGuard().run_guard('VAL "USR 32768"')[0], 8)

    def test_arithmetic_text_is_forwarded_to_48k_rom(self):
        self.assertEqual(ValNativeGuard().run_guard('2 + 3 * 4'), (0x35DE, 0x1D))

    def test_executable_literal_machine_call_stays_blocked(self):
        with self.assertRaises(UnsafeVal):
            audit('PRINT VAL "USR 32768"')

    def test_quoted_remark_is_not_executable(self):
        self.assertEqual(audit('PRINT "VAL USR 30000": REM VAL "USR 40000"'), [])

    def test_nested_numeric_val_remains_supported(self):
        """A legal nested VAL must eventually be accepted, without allowing USR."""
        self.assertEqual(ValNativeGuard().run_guard('VAL "2+3"')[0], 0x35DE)


if __name__ == '__main__':
    unittest.main()

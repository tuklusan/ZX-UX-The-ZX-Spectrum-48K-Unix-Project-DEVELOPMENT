"""Mandatory VAL behavior. These must fail until dynamic VAL is safe."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from val_guard import guard_val, UnsafeVal


def audit(text):
    return guard_val([(10, text.encode('latin1'))], {})


class Round2Val(unittest.TestCase):
    def test_variable_string_numeric_expression_is_allowed(self):
        audit('10 PRINT VAL A$'.removeprefix('10 '))

    def test_input_variable_string_is_allowed(self):
        audit('INPUT A$: PRINT VAL A$')

    def test_constant_expression_is_allowed(self):
        audit('LET X=VAL "2+3*4"')

    def test_nested_expression_is_allowed(self):
        audit('PRINT VAL ("PI/2")')

    def test_dynamic_text_rejects_usr_when_evaluated(self):
        from val_runtime import RestrictedValRuntime, BlockedMachineCall
        evaluator = RestrictedValRuntime()
        with self.assertRaises(BlockedMachineCall):
            evaluator.evaluate('USR 32768')

    def test_runtime_nested_constructed_usr_stays_blocked(self):
        from val_runtime import RestrictedValRuntime, BlockedMachineCall
        evaluator = RestrictedValRuntime()
        with self.assertRaises(BlockedMachineCall):
            evaluator.evaluate('VAL "USR 32768"')

    def test_runtime_numeric_expression_evaluation(self):
        from val_runtime import RestrictedValRuntime
        evaluator = RestrictedValRuntime()
        self.assertEqual(evaluator.evaluate('2 + 3 * 4'), 14)

    def test_executable_machine_code_stays_blocked(self):
        with self.assertRaises(UnsafeVal):
            audit('PRINT VAL "USR 32768"')

    def test_quoted_remark_is_not_an_executable_instruction(self):
        audit('PRINT "VAL USR 30000": REM VAL "USR 40000"')


if __name__ == '__main__':
    unittest.main()

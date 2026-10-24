"""Executable Z80 checks against the guarded runtime VAL code, not mock emitters."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from native_val_rt import _guard_code


class ValNativeGuard(unittest.TestCase):
    def run_guard(self, expression):
        from z80asm import asm
        from z80mini import Z80
        data = expression if isinstance(expression, bytes) else expression.encode('ascii')
        mem = bytearray(65536)
        image = _guard_code(asm)
        mem[0x9000:0x9000 + len(image)] = image
        mem[0x8000:0x8000 + len(data)] = data
        stkend = 0x8105
        mem[0x5C65:0x5C67] = stkend.to_bytes(2, 'little')
        mem[stkend - 5:stkend] = bytes((0x00, 0x00, 0x80)) + len(data).to_bytes(2, 'little')
        before = mem[stkend - 5:stkend]
        cpu = Z80(mem)
        cpu.pc = 0x9000
        for _ in range(10000):
            if cpu.pc in (0x35DE, 0x0008):
                break
            cpu.step()
        else:
            self.fail('native VAL guard never reached ROM evaluator or rejection')
        self.assertEqual(mem[stkend - 5:stkend], before)
        self.assertEqual(mem[0x5C65:0x5C67], stkend.to_bytes(2, 'little'))
        return cpu.pc, cpu.b

    def test_arithmetic_passes_unchanged(self):
        self.assertEqual(self.run_guard(' 2+3*4 '), (0x35DE, 0x1D))
        self.assertEqual(self.run_guard('SIN PI/2'), (0x35DE, 0x1D))

    def test_machine_code_call_rejected(self):
        for value in ('USR 32768', 'usr 32768', b'\xc032768'):
            with self.subTest(value=value):
                self.assertEqual(self.run_guard(value)[0], 0x0008)

    def test_constructed_val_rejected_before_rom(self):
        for value in ('VAL A$', 'val a$', b'\xb0 A$'):
            with self.subTest(value=value):
                self.assertEqual(self.run_guard(value)[0], 0x0008)

    def test_words_inside_non_executed_quotes_are_not_blocked(self):
        self.assertEqual(self.run_guard('CODE "USR VAL"')[0], 0x35DE)

    def test_safe_direct_literal_nested_val(self):
        for source in ('VAL "2+3"', 'val  "PI/2"', b'\xb0 "3*4"'):
            with self.subTest(source=source):
                self.assertEqual(self.run_guard(source), (0x35DE, 0x1D))

    def test_nested_unsafe_code_before_rom(self):
        for source in ('VAL "USR 32768"', 'VAL "2+USR 32768"',
                       'VAL "VAL A$"', 'VAL "VAL \"USR 32768\""',
                       b'\xb0 "\xc0 32768"', 'VAL A$', 'VAL ("USR 32768")'):
            with self.subTest(source=source):
                self.assertEqual(self.run_guard(source)[0], 0x0008)

    def test_nested_numeric_literals_with_direct_machine_code_blocked(self):
        self.assertEqual(self.run_guard('VAL "2+3" + USR 32768')[0], 0x0008)
        self.assertEqual(self.run_guard('VAL "2+3" + VAL A$')[0], 0x0008)

    def test_empty_value_is_left_to_original_rom(self):
        self.assertEqual(self.run_guard('')[0], 0x35DE)


if __name__ == '__main__':
    unittest.main()

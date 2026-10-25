"""Compile constant numeric DATA arithmetic using the actual 48K ROM calculator.

The BASIC program and its Sinclair numeric metadata are not rewritten. This
extension is deliberately restricted to literal arithmetic: names, functions,
comparisons and any value determined at READ time remain unsupported.
"""
from __future__ import annotations

# Spectrum 48K ROM calculator instructions (RST 28).
C_ADDITION, C_SUBTRACT, C_MULTIPLY, C_DIVISION = 0x0f, 0x03, 0x04, 0x05

_BINARY = {ord('+'): (1, C_ADDITION), ord('-'): (1, C_SUBTRACT),
           ord('*'): (2, C_MULTIPLY), ord('/'): (2, C_DIVISION)}


def with_literal_data_expressions(base):
    class LiteralData(base):
        def st_data(self):
            was_data = getattr(self, '_zxux_in_data', False)
            self._zxux_in_data = True
            try:
                return super().st_data()
            finally:
                self._zxux_in_data = was_data

        def number_maybe_val(self):
            if not getattr(self, '_zxux_in_data', False):
                return super().number_maybe_val()
            value = self._zxux_data_expression(0)
            self.calc.append(value)
            self.classify_const()

        def _zxux_data_atom(self):
            token = self.get_char()
            if token in (ord('-'), ord('+')):
                self.next_char()
                value = self._zxux_data_atom()
                return self.fp.negate(value) if token == ord('-') else value
            if token == ord('('):
                self.next_char()
                value = self._zxux_data_expression(0)
                if self.get_char() != ord(')'):
                    self.not_supported('DATA expression parentheses')
                self.next_char()
                return value
            # Use the unchanged HiSoft parser for literal Sinclair floating
            # point encodings and for its historical VAL "constant" extension.
            if self.not_number() and token != 0xB0:
                self.not_supported('DATA expression requires numeric literals')
            before = len(self.calc)
            super().number_maybe_val()
            if len(self.calc) != before + 1:
                self.not_supported('DATA expression literal')
            return self.calc.pop()

        def _zxux_data_expression(self, min_bp):
            lhs = self._zxux_data_atom()
            while True:
                pair = _BINARY.get(self.get_char())
                if pair is None or pair[0] < min_bp:
                    return lhs
                precedence, rom_operator = pair
                self.next_char()
                rhs = self._zxux_data_expression(precedence + 1)
                lhs = self.fp.calc([lhs, rhs], [rom_operator])[-1]

    return LiteralData

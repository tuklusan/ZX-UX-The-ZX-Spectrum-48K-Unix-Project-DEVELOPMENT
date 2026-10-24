"""Spectrum 48K FOR/NEXT control records, independent of lexical nesting.

A FOR record belongs to its single-letter numeric variable; GO TO and
GO SUB do not alter it. NEXT looks up that record at execution time.
This model is a test reference, not a substitute for emitted native Z80.
"""
from dataclasses import dataclass
import math


@dataclass
class _Control:
    limit: float
    step: float
    body: int


class ProcessLoopStack:
    def __init__(self):
        self.controls = {}
        self.values = {}

    @staticmethod
    def _letter(name):
        if not isinstance(name, str) or len(name) != 1 or not name.isascii() or not name.isalpha():
            raise ValueError('FOR/NEXT control variable must be one letter')
        return name.upper()

    @staticmethod
    def _number(value):
        value = float(value)
        if not math.isfinite(value):
            raise ValueError('Invalid FOR/NEXT numeric value')
        return value

    def enter(self, name, first, limit, step, body):
        key = self._letter(name)
        first, limit, step = (self._number(value) for value in (first, limit, step))
        self.values[key] = first
        self.controls[key] = _Control(limit, step, body)
        # Spectrum skips the body when the initial control value is beyond
        # the limit in the chosen direction. The 48K interpreter searches
        # forward for the matching NEXT at execution time in that case.
        return (step >= 0 and first <= limit) or (step < 0 and first >= limit)

    def assign(self, name, value):
        key = self._letter(name)
        self.values[key] = self._number(value)

    def value(self, name):
        return self.values[self._letter(name)]

    def next(self, name):
        key = self._letter(name)
        if key not in self.controls:
            raise ValueError('1 NEXT without FOR')
        control = self.controls[key]
        value = self._number(self.values[key] + control.step)
        self.values[key] = value
        if (control.step >= 0 and value <= control.limit or
                control.step < 0 and value >= control.limit):
            return control.body
        del self.controls[key]
        return None

    def jump(self, line):
        return line

    def run(self):
        self.controls.clear()
        self.values.clear()

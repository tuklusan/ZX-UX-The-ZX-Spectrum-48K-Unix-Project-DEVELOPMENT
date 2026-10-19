"""Compiler rejects provably invalid ZX-UX API constants, not expressions."""
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'release/src/zx-ux-sdk'))
from rcc.driver import compile_to_asm
from rcc.lex import CError


class ConstantRangeTests(unittest.TestCase):
    def compile(self, statement):
        with tempfile.TemporaryDirectory() as temp:
            src = pathlib.Path(temp) / 'check.c'
            src.write_text('#include <c48.h>\nint main(void){ int x; x=7; '
                           + statement + ';return 0;}\n')
            return compile_to_asm(str(src))

    def test_literal_and_folded_invalid_values_are_rejected(self):
        for stmt in ('ink(9)', 'ink(-1)', 'ink(4+5)', 'paper(8)',
                     'border(8)', 'bright(2)', 'flash(-1)', 'inverse(3)',
                     'over(2)', 'print_at(24,0,"bad")',
                     'print_at(0,64,"bad")', 'plot(256,0)',
                     'udg_define(32,0)', 'udg_draw(0,24,0)'):
            with self.subTest(statement=stmt):
                with self.assertRaisesRegex(CError, 'constant outside'):
                    self.compile(stmt)

    def test_allowed_and_dynamic_values_still_compile(self):
        for stmt in ('ink(7)', 'paper(0)', 'border(7)',
                     'bright(1)', 'flash(0)', 'ink(x)',
                     'paper(x+2)', 'plot(x,175)', 'point(x,0)',
                     'print_at(23,63,"ok")'):
            with self.subTest(statement=stmt):
                self.compile(stmt)


if __name__ == '__main__':
    unittest.main()

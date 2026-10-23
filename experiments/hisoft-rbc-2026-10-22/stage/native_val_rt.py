"""Use HiSoft's existing runtime VAL support for non-literal string operands.

HiSoft v1.1 accepts VAL "123" at compile time, but rejects VAL x$.
The compiler's runtime VAL entry is already used by numeric INPUT, and
is therefore reused here without touching archived BASIC files.
"""
from __future__ import annotations


def install(compiler):
    from rtnames import RT
    base = compiler.Compiler
    original = base.fn_val
    if getattr(original, "_zxux_runtime_val", False):
        return

    def fn_val(self):
        if self.val_directive or self.get_char() == ord('"'):
            return original(self)
        self.operand()
        if self.t != compiler.STRING:
            self.not_supported('VAL operand must be a string')
        self.call_rt(RT.VAL)
        self.t = compiler.REAL

    fn_val._zxux_runtime_val = True
    base.fn_val = fn_val

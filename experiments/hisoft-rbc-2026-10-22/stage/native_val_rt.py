"""Support HiSoft v1.1's omitted dynamic VAL routine on Spectrum 48K.

The stock v1.1 compiler leaves runtime slot 109 empty. The 48K ROM provides
VAL X$ at 0x35DE with B=0x18. Emit an actual native tail call to that ROM
entry so the same syntax checks and expression evaluator are used as BASIC.
"""
from __future__ import annotations


def install(compiler):
    from rtnames import RT
    from z80asm import asm
    native_val = asm('ld b,$18; jp $35de')
    assert bytes(native_val) == bytes((0x06, 0x18, 0xC3, 0xDE, 0x35))
    base = compiler.rtlib.Machine
    if not getattr(base, '_zxux_native_val', False):
        class ZXUXValMachine(base):
            _zxux_native_val = True

            def run_emitter(self, n, pc, counting, code_base):
                if n != RT.VAL:
                    return super().run_emitter(n, pc, counting, code_base)
                if not counting and not self.de_flags & 1:
                    self.far[pc:pc + len(native_val)] = native_val
                return pc + len(native_val)

        compiler.rtlib.Machine = ZXUXValMachine

    fn = compiler.Compiler.fn_val
    if getattr(fn, '_zxux_native_val', False):
        return

    def native_fn_val(self):
        # Preserve HiSoft's fast path for numeric literals and any explicitly
        # requested VAL directive. Only string expressions need the new RT.
        if self.val_directive or self.get_char() == ord('"'):
            return fn(self)
        self.operand()
        if self.t != compiler.STRING:
            self.not_supported('VAL operand must be a string')
        self.call_rt(RT.VAL)
        self.t = compiler.REAL

    native_fn_val._zxux_native_val = True
    compiler.Compiler.fn_val = native_fn_val
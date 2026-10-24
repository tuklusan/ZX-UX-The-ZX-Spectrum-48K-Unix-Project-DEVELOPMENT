"""Runtime-only Spectrum control-flow and guarded string VAL extensions.

These extensions operate after genuine tokenization and ROM syntax checking.
They do not modify numbered BASIC source or allow numeric machine-code USR.
"""
from __future__ import annotations


def guarded_val_bytes():
    """Inspect the evaluated string bytes before calling the 48K ROM VAL.

    The floating-point calculator stack's last value is the 5-byte string
    descriptor; STKEND is in the standard Spectrum system variable. A USR
    token outside quotes must never reach the ROM numeric expression evaluator.
    """
    code = bytearray()
    labels = {}
    jumps = []

    def emit(*values):
        code.extend(values)

    def mark(label):
        labels[label] = len(code)

    def jr(opcode, label):
        emit(opcode, 0)
        jumps.append((len(code) - 1, label))

    emit(0xF5, 0xC5, 0xD5, 0xE5)    # preserve AF, BC, DE, HL
    emit(0x2A, 0x65, 0x5C)          # HL=(STKEND)
    emit(0x2B, 0x46, 0x2B, 0x4E)    # BC=string byte count
    emit(0x2B, 0x56, 0x2B, 0x5E)    # DE=string address
    emit(0xEB, 0x16, 0x00)          # HL=string address; D=quote state
    mark('scan')
    emit(0x78, 0xB1)                # A=B | C, done if length zero
    jr(0x28, 'allowed')
    emit(0x7E, 0xFE, 0x22)          # quote toggles quote state
    jr(0x20, 'not_quote')
    emit(0x7A, 0xEE, 0x01, 0x57)
    jr(0x18, 'next')
    mark('not_quote')
    emit(0x7A, 0xB7)
    jr(0x20, 'next')                # a quoted occurrence is text
    emit(0x7E, 0xFE, 0xEA)          # REM token: nonexecuted suffix
    jr(0x28, 'allowed')
    emit(0xFE, 0xC0)                # executable USR keyword token
    jr(0x28, 'blocked')
    emit(0xFE, 0xB0)                # nested VAL may evaluate an inner USR
    jr(0x28, 'blocked')
    emit(0xFE, 0xAE)                # VAL$ can execute a nested expression
    jr(0x28, 'blocked')
    mark('next')
    emit(0x23, 0x0B)                # advance input and decrease length
    jr(0x18, 'scan')
    mark('allowed')
    emit(0xE1, 0xD1, 0xC1, 0xF1)    # restore all registers
    emit(0x06, 0x1D, 0xC3, 0xDE, 0x35)  # invoke ROM VAL X$
    mark('blocked')
    emit(0xE1, 0xD1, 0xC1, 0xF1)
    emit(0xCF, 0x0A)                # Spectrum handled invalid-argument error
    for where, name in jumps:
        distance = labels[name] - (where + 1)
        if not -128 <= distance <= 127:
            raise AssertionError('Z80 runtime branch too far')
        code[where] = distance & 255
    assert code[:7] == bytes.fromhex('f5 c5 d5 e5 2a 65 5c')
    return bytes(code)


def install(compiler):
    """Modify only HiSoft's native emission paths; no source-level rewrites."""
    from rtnames import RT
    val_bytes = guarded_val_bytes()
    machine = compiler.rtlib.Machine
    if not getattr(machine, '_zxux_guarded_val', False):
        class GuardedMachine(machine):
            _zxux_guarded_val = True

            def run_emitter(self, n, pc, counting, code_base):
                if n != RT.VAL:
                    return super().run_emitter(n, pc, counting, code_base)
                if not counting and not self.de_flags & 1:
                    self.far[pc:pc + len(val_bytes)] = val_bytes
                return pc + len(val_bytes)

        compiler.rtlib.Machine = GuardedMachine

    cls = compiler.Compiler
    if getattr(cls, '_zxux_runtime_control', False):
        return
    reset = cls.reset
    val = cls.fn_val
    for_begin = cls.st_for
    for_end = cls.st_next
    run_pass = cls.run_pass

    def spectrum_reset(self, program):
        reset(self, program)
        # This is HiSoft's own table-driven runtime dispatch, not a guessed
        # rewrite of computed line numbers into constants.
        self.goto_directive = 1
        self.gosub_all = 1
        self.restore_directive = 1
        self.restore_all = 1
        self._zxux_unclosed_for = {}

    def spectrum_val(self):
        if self.val_directive or self.get_char() == ord('"'):
            return val(self)
        self.operand()
        if self.t != compiler.STRING:
            self.not_supported('VAL operand must be a string expression')
        self.call_rt(RT.VAL)
        self.t = compiler.REAL

    def spectrum_for(self):
        key = compiler.letter(self.get_char())
        descriptor = self.fors[key]
        if descriptor['flags'] & 0x80:
            # Sinclair FOR replaces the previous variable's loop descriptor.
            # The old conditional jump must not retain its unresolved $FFFF.
            previous = self._zxux_unclosed_for.get(key)
            if previous is not None and self.storing:
                target = (self.pc + self.code_base) & 0xFFFF
                self.far[previous:previous + 2] = target.to_bytes(2, 'little')
            descriptor['flags'] &= 0x7F
        for_begin(self)
        self._zxux_unclosed_for[key] = self.pc - 2

    def spectrum_next(self):
        key = compiler.letter(self.get_char())
        for_end(self)
        self._zxux_unclosed_for.pop(key, None)

    def spectrum_pass(self):
        run_pass(self)
        if self.storing:
            for key, where in self._zxux_unclosed_for.items():
                # An unmatched FOR is syntactically valid. It must not
                # branch through an unpatched $FFFF target at runtime.
                target = (where + 2 + self.code_base) & 0xFFFF
                self.far[where:where + 2] = target.to_bytes(2, 'little')

    cls.reset = spectrum_reset
    cls.fn_val = spectrum_val
    cls.st_for = spectrum_for
    cls.st_next = spectrum_next
    cls.run_pass = spectrum_pass
    cls._zxux_runtime_control = True
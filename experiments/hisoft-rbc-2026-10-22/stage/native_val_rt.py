"""Guard dynamic Sinclair VAL before entering the 48K ROM evaluator.

The ROM evaluator can execute numeric USR.  The runtime must not expose that
entry to untrusted strings.  This is a deliberately conservative first stage:
nested runtime VAL is rejected (even when harmless) because it can construct
USR after the initial string was checked.  The full 48K VAL language therefore
remains an open gate until nested safe evaluation has been implemented.
"""
from __future__ import annotations


def _guard_code(asm):
    """Z80 byte validator for a ROM calculator-stack string descriptor.

    STKEND (23653) points one byte beyond the five-byte string value:
    type, pointer low/high, length low/high.  Unlike STK-FETCH at $2BF1,
    reading this descriptor does not consume the calculator operand.
    RST 8 with report code $0B stops an unsafe expression before $35DE.
    """
    out = bytearray()
    labels = {}
    fixes = []

    def emit(source):
        out.extend(asm(source))

    def mark(name):
        if name in labels:
            raise ValueError(f'duplicate runtime label: {name}')
        labels[name] = len(out)

    def jr(target, cond=None):
        opcode = {'': 0x18, 'nz': 0x20, 'z': 0x28, 'nc': 0x30, 'c': 0x38}[cond or '']
        fixes.append((len(out), target))
        out.extend((opcode, 0))

    emit('ld hl,($5c65); dec hl; ld b,(hl); dec hl; ld c,(hl); '
         'dec hl; ld d,(hl); dec hl; ld e,(hl); ld h,0')
    mark('scan')
    emit('ld a,b; or c')
    jr('allowed', 'z')
    emit('ld a,(de); cp 34')
    jr('quote', 'z')
    emit('ld a,h; or a')
    jr('advance', 'nz')
    emit('ld a,(de); cp $c0')  # token USR
    jr('blocked', 'z')
    emit('cp $b0')            # token VAL
    jr('blocked', 'z')
    emit('cp $ae')            # token VAL$
    jr('blocked', 'z')
    emit('and $df; cp 85')    # 'U', ASCII or lowercase
    jr('usr', 'z')
    emit('cp 86')             # 'V'
    jr('val', 'z')
    jr('advance')
    mark('usr')
    emit('ld a,b; or a')
    jr('usr_bytes', 'nz')
    emit('ld a,c; cp 3')
    jr('advance', 'c')
    mark('usr_bytes')
    emit('push de; inc de; ld a,(de); and $df; cp 83') # 'S'
    jr('usr_restore', 'nz')
    emit('inc de; ld a,(de); and $df; cp 82')          # 'R'
    jr('usr_restore', 'nz')
    emit('pop de')
    jr('blocked')
    mark('usr_restore')
    emit('pop de')
    jr('advance')
    mark('val')
    emit('ld a,b; or a')
    jr('val_bytes', 'nz')
    emit('ld a,c; cp 3')
    jr('advance', 'c')
    mark('val_bytes')
    emit('push de; inc de; ld a,(de); and $df; cp 65') # 'A'
    jr('val_restore', 'nz')
    emit('inc de; ld a,(de); and $df; cp 76')           # 'L'
    jr('val_restore', 'nz')
    emit('pop de')
    jr('blocked')
    mark('val_restore')
    emit('pop de')
    jr('advance')
    mark('quote')
    emit('ld a,h; xor 1; ld h,a')
    mark('advance')
    emit('inc de; dec bc')
    jr('scan')
    mark('allowed')
    emit('ld b,$1d; jp $35de')
    mark('blocked')
    emit('rst 8; defb $0b')
    for pos, name in fixes:
        if name not in labels:
            raise ValueError(f'undefined VAL guard jump: {name}')
        distance = labels[name] - (pos + 2)
        if not -128 <= distance <= 127:
            raise ValueError(f'VAL guard relative jump exceeds Z80 range: {name} {distance}')
        out[pos + 1] = distance & 255
    return bytes(out)


def install(compiler):
    from rtnames import RT
    from z80asm import asm
    native_val = _guard_code(asm)
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
        if self.val_directive or self.get_char() == ord('"'):
            return fn(self)
        self.operand()
        if self.t != compiler.STRING:
            self.not_supported('VAL operand must be a string')
        self.call_rt(RT.VAL)
        self.t = compiler.REAL

    native_fn_val._zxux_native_val = True
    compiler.Compiler.fn_val = native_fn_val

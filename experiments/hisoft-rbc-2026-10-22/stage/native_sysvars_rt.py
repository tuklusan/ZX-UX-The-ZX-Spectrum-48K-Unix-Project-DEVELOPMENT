"""Native private PEEK/POKE for Spectrum keyboard and 24-bit frame counter.

HiSoft 48K v1.1 has unused runtime slots 42 and 43; reuse them to
centralize native PEEK and POKE dispatch without rewriting SSX bytes.
The two slots are checked for emptiness at installation. All virtual bytes
live in compiler-allocated process BSS, not ROM or kernel system RAM.
"""
from __future__ import annotations

from spectrum_sysvars import FLAGS2, PIP, FRAMES, PRIVATE

PEEK_RT = 42
POKE_RT = 43
# flags2, pip, three FRAMES bytes, last 16-bit tick, initialized marker
BSS_BYTES = 8


class _Code:
    def __init__(self, asm):
        self.asm = asm
        self.code = bytearray()
        self.labels = {}
        self.jumps = []
        self.absrefs = []

    def op(self, text):
        self.code.extend(self.asm(text))

    def address(self, text, offset):
        part = self.asm(text)
        if part[-2:] != b'\x00\x00':
            raise AssertionError(f'assembler address operand changed: {text}')
        self.absrefs.append((len(self.code)+len(part)-2, offset))
        self.code.extend(part)

    def label(self, name):
        if name in self.labels:
            raise AssertionError('duplicate Z80 label ' + name)
        self.labels[name] = len(self.code)

    def jr(self, target, condition=''):
        opcode = {'': 0x18, 'nz': 0x20, 'z': 0x28, 'nc': 0x30, 'c': 0x38}[condition]
        self.jumps.append((len(self.code), target))
        self.code.extend((opcode,0))

    def build(self, base, load):
        data = bytearray(self.code)
        for pos, target in self.jumps:
            if target not in self.labels:
                raise AssertionError('missing native branch label: ' + target)
            delta = self.labels[target] - (pos + 2)
            if not -128 <= delta <= 127:
                raise AssertionError(f'native Z80 branch out of range: {target} {delta}')
            data[pos+1] = delta & 255
        for pos, index in self.absrefs:
            ptr = (base + load + index) & 65535
            data[pos:pos+2] = bytes((ptr & 255, ptr >> 8))
        return bytes(data)


def _clock_sync(e):
    """Preserve all live input registers and update process 24-bit FRAMES."""
    e.op('push af; push bc; push de; push hl')
    e.op('ld a,38; call $6003')
    e.address('ld a,($0000)', 7)
    e.op('or a')
    e.jr('tick_known','nz')
    e.op('ld a,1')
    e.address('ld ($0000),a',7)
    e.address('ld ($0000),hl',5)
    e.jr('tick_done')
    e.label('tick_known')
    e.address('ld de,($0000)', 5)
    e.address('ld ($0000),hl', 5)
    e.op('or a; sbc hl,de')
    e.address('ld a,($0000)',2)
    e.op('add a,l')
    e.address('ld ($0000),a',2)
    e.address('ld a,($0000)',3)
    e.op('adc a,h')
    e.address('ld ($0000),a',3)
    e.address('ld a,($0000)',4)
    e.op('adc a,0')
    e.address('ld ($0000),a',4)
    e.label('tick_done')
    e.op('pop hl; pop de; pop bc; pop af')


def _process_address_check(e, base, total, accepted):
    """Let unmodified RAM instructions see only native process-owned memory."""
    if total < 1:
        # Counting passes may not yet know BSS bounds; code length is stable.
        total = 1
    e.op('push de; push hl')
    e.address('ld de,$0000', -base)
    e.op('or a; sbc hl,de; pop hl')
    e.jr('out_of_process', 'c')
    e.op('push hl')
    e.address('ld de,$0000', total-1-base)
    e.op('or a; sbc hl,de; pop hl')
    e.jr('range_ok','c')
    e.jr('range_ok','z')
    e.label('out_of_process')
    e.op('pop de; rst 8; defb $0b')
    e.label('range_ok')
    e.op('pop de')
    e.jr(accepted)


def _native_peek(asm, base, load, total=0):
    e = _Code(asm)
    e.op('ld a,h; cp $5c')
    e.jr('ordinary_bridge','nz')
    e.op('ld a,l; cp $04')
    e.jr('kstate','z')
    e.op('cp $39')
    e.jr('pip','z')
    e.op('cp $6a')
    e.jr('flags','z')
    e.op('cp $78')
    e.jr('ordinary_bridge','c')
    e.op('cp $7b')
    e.jr('ordinary_bridge','nc')
    _clock_sync(e)
    e.op('ld a,l; cp $78')
    e.jr('frames0','z')
    e.op('cp $79')
    e.jr('frames1','z')
    e.address('ld a,($0000)',4)
    e.jr('result')
    e.label('frames0')
    e.address('ld a,($0000)',2)
    e.jr('result')
    e.label('frames1')
    e.address('ld a,($0000)',3)
    e.jr('result')
    e.label('pip')
    e.address('ld a,($0000)',1)
    e.jr('result')
    e.label('flags')
    e.address('ld a,($0000)',0)
    e.label('result')
    e.op('ld l,a; ld h,0; ret')
    e.label('ordinary_bridge')
    e.jr('ordinary')
    e.label('kstate')
    # Preserve the earlier ROM keyboard-scan service for the original 48K
    # last-key byte. Never treat arbitrary 0x5Cxx addresses as readable.
    e.op('push bc; push de; push hl; call $02bf; pop hl; pop de; pop bc')
    e.op('ld l,(hl); ld h,0; ret')
    e.label('ordinary')
    # ROM and bitmap/attribute reads are public; other addresses must be
    # inside the process's compiler-allocated image/BSS, never ZX-UX globals.
    e.op('ld a,h; cp $5b')
    e.jr('read_public','c')
    _process_address_check(e, base, total, 'read_public')
    e.label('read_public')
    e.op('ld l,(hl); ld h,0; ret')
    return e.build(base,load)


def _native_poke(asm, base, load, total=0):
    e = _Code(asm)
    e.op('ld a,h; cp $5c')
    e.jr('ordinary','nz')
    e.op('ld a,l; cp $39')
    e.jr('pip','z')
    e.op('cp $6a')
    e.jr('flags','z')
    e.op('cp $78')
    e.jr('ordinary','c')
    e.op('cp $7b')
    e.jr('ordinary','nc')
    _clock_sync(e)
    e.op('ld a,l; cp $78')
    e.jr('frames0','z')
    e.op('cp $79')
    e.jr('frames1','z')
    e.op('ld a,e')
    e.address('ld ($0000),a',4)
    e.op('ret')
    e.label('frames0')
    e.op('ld a,e')
    e.address('ld ($0000),a',2)
    e.op('ret')
    e.label('frames1')
    e.op('ld a,e')
    e.address('ld ($0000),a',3)
    e.op('ret')
    e.label('pip')
    e.op('ld a,e')
    e.address('ld ($0000),a',1)
    e.op('ret')
    e.label('flags')
    e.op('ld a,e')
    e.address('ld ($0000),a',0)
    e.op('ret')
    e.label('ordinary')
    # Writes to ROM or protected machine state must never reach physical RAM.
    # Screen bitmap/attributes and private executable memory are separate.
    e.op('ld a,h; cp $40')
    e.jr('blocked_rom','c')
    e.op('cp $5b')
    e.jr('write_public','c')
    _process_address_check(e, base, total, 'write_public')
    e.label('write_public')
    e.op('ld (hl),e; ret')
    e.label('blocked_rom')
    e.op('rst 8; defb $0b')
    return e.build(base,load)


def install(compiler):
    """Install direct runtime PEEK/POKE hooks for the 48K compiler only."""
    from z80asm import asm
    base = compiler.rtlib.Machine
    if not getattr(base,'_zxux_sysvars',False):
        class PrivateSysvarMachine(base):
            _zxux_sysvars = True
            _zxux_sysvar_base = 0
            _zxux_total = 0

            def run_emitter(self, n, pc, counting, code_base):
                if n not in (PEEK_RT,POKE_RT):
                    return super().run_emitter(n,pc,counting,code_base)
                if self.emitter(n):
                    raise ValueError('RBC reserved 48K runtime slot is not empty')
                if not getattr(self.img,'v11',False):
                    raise ValueError('RBC system virtualization requires HiSoft 48K v1.1')
                fn = _native_peek if n == PEEK_RT else _native_poke
                emitted = fn(asm, self._zxux_sysvar_base, code_base, self._zxux_total)
                if not counting and not self.de_flags & 1:
                    self.far[pc:pc+len(emitted)] = emitted
                return pc + len(emitted)
        compiler.rtlib.Machine = PrivateSysvarMachine

    cls = compiler.Compiler
    if getattr(cls,'_zxux_sysvars',False):
        return
    old_reset, old_layout = cls.reset, cls.layout_vars

    def reset(self, prog):
        old_reset(self,prog)
        self._zxux_sysvar_base = 0
        self.m._zxux_sysvar_base = 0
        self.m._zxux_total = 0

    def layout_vars(self):
        old_layout(self)
        if self.m.used(PEEK_RT) or self.m.used(POKE_RT):
            self._zxux_sysvar_base = self.pc
            self.m._zxux_sysvar_base = self.pc
            self.pc = (self.pc + BSS_BYTES) & 65535
            self.m._zxux_total = self.pc

    def fn_peek(self):
        self.operand_to_int()
        self.call_rt(PEEK_RT)
        self.t = compiler.POSINT

    def st_poke(self):
        self.expr_int()
        self.emit('push hl')
        self.next_char()
        self.expr_int()
        self.emit('ld e,l; pop hl')
        self.call_rt(POKE_RT)

    cls.reset = reset
    cls.layout_vars = layout_vars
    cls.fn_peek = fn_peek
    cls.st_poke = st_poke
    cls._zxux_sysvars = True

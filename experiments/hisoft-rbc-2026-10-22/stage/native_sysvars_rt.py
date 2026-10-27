"""Native private PEEK/POKE for Spectrum keyboard and 24-bit frame counter.

HiSoft 48K v1.1 has unused runtime slots 42 and 43; reuse them to
centralize native PEEK and POKE dispatch without rewriting SSX bytes.
The two slots are checked for emptiness at installation. All virtual bytes
live in compiler-allocated process BSS, not ROM or kernel system RAM.
"""
from __future__ import annotations

from spectrum_sysvars import FLAGS2, PIP, FRAMES, SCR_CT, PRIVATE
from native_error_exit import error_exit_asm

PEEK_RT = 42
POKE_RT = 43
# flags2, pip, three FRAMES bytes, last 16-bit tick, initialized marker
BSS_BYTES = 14


class _Code:
    def __init__(self, asm):
        self.asm = asm
        self.code = bytearray()
        self.labels = {}
        self.jumps = []
        self.absrefs = []
        self.absjumps = []
        self.source = []  # Typed emitter statements, not a decoded output image.

    def op(self, text):
        self.code.extend(self.asm(text))
        self.source.extend(('op', part.strip()) for part in text.split(';')
                           if part.strip())

    def address(self, text, offset):
        part = self.asm(text)
        if part[-2:] != b'\x00\x00':
            raise AssertionError(f'assembler address operand changed: {text}')
        self.absrefs.append((len(self.code)+len(part)-2, offset))
        self.source.append(('address', text, offset))
        self.code.extend(part)

    def label(self, name):
        if name in self.labels:
            raise AssertionError('duplicate Z80 label ' + name)
        self.labels[name] = len(self.code)
        self.source.append(('label', name))

    def jr(self, target, condition=''):
        opcode = {'': 0x18, 'nz': 0x20, 'z': 0x28, 'nc': 0x30, 'c': 0x38}[condition]
        self.jumps.append((len(self.code), target))
        self.source.append(('jr', condition, target))
        self.code.extend((opcode,0))

    def jp(self, name, condition=''):
        opcode = {'':0xc3,'z':0xca,'nz':0xc2,'c':0xda,'nc':0xd2}[condition]
        self.absjumps.append((len(self.code)+1,name))
        self.source.append(('jp', condition, name))
        self.code.extend((opcode,0,0))

    def assembly(self, bss_offset: int, entry_offset: int):
        """Z80 source with named branches and process-relative word operands.

        The start label is the runtime's actual position in the whole text.
        A BSS reference uses its offset relative to that entry; native ras/rld
        recomputes the final address after every safe text-size change.
        """
        result = ['  section text', '  global start', 'start:']
        for item in self.source:
            kind = item[0]
            if kind == 'label':
                result.append('rbc_local_' + item[1] + ':')
            elif kind == 'op':
                result.append('  ' + item[1])
            elif kind == 'address':
                source, offset = item[1:]
                if source.count('$0000') != 1:
                    raise ValueError('runtime address source has no exact operand')
                displacement = bss_offset - entry_offset + offset
                result.append('  ' + source.replace('$0000',
                                                     'start+' + str(displacement)))
            elif kind in ('jp', 'jr'):
                condition, target = item[1:]
                result.append('  ' + kind + ' ' +
                              (condition + ',' if condition else '') +
                              'rbc_local_' + target)
            else:
                raise ValueError('untyped native runtime statement')
        return '\n'.join(result) + '\n'

    def build(self, base, load, entry=0):
        data = bytearray(self.code)
        for pos, target in self.jumps:
            if target not in self.labels:
                raise AssertionError('missing native branch label: ' + target)
            delta = self.labels[target] - (pos + 2)
            if not -128 <= delta <= 127:
                raise AssertionError(f'native Z80 branch out of range: {target} {delta}')
            data[pos+1] = delta & 255
        for pos, name in self.absjumps:
            if name not in self.labels:
                raise AssertionError('missing absolute native label: '+name)
            address=(load+entry+self.labels[name]) & 65535
            data[pos:pos+2] = address.to_bytes(2,'little')
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


def _native_error_exit(e):
    """Restore global graphics via the SSX wrapper before native exit."""
    e.op(error_exit_asm(11))


def _process_address_check(e, base, total, accepted, prefix=""):
    """Let unmodified RAM instructions see only native process-owned memory."""
    if total < 1:
        # Counting passes may not yet know BSS bounds; code length is stable.
        total = 1
    e.op('push de; push hl')
    e.address('ld de,$0000', -base)
    e.op('or a; sbc hl,de; pop hl')
    e.jr('out_of_process'+prefix, 'c')
    e.op('push hl')
    e.address('ld de,$0000', total-1-base)
    e.op('or a; sbc hl,de; pop hl')
    e.jr('range_ok'+prefix,'c')
    e.jr('range_ok'+prefix,'z')
    e.label('out_of_process'+prefix)
    e.op('pop de')
    _native_error_exit(e)
    e.label('range_ok'+prefix)
    e.op('pop de')
    e.jr(accepted)


def _cache_font_pointer(e, suffix):
    """Save SSX startup's real private font pointer before BASIC switches CHARS."""
    e.address('ld a,($0000)',13)
    e.op('or a')
    e.jr('font_cached_'+suffix,'nz')
    e.op('push hl')
    e.op('ld hl,($5c36)')
    e.address('ld ($0000),hl',11)
    e.op('ld a,1')
    e.address('ld ($0000),a',13)
    e.op('pop hl')
    e.label('font_cached_'+suffix)


def _select_print_font(e):
    """ROM CHARS selects ROM printing; all other values select private font."""
    _cache_font_pointer(e, 'write')
    e.address('ld a,($0000)',10)
    e.op('or a')
    e.jr('font_hi_override','nz')
    e.op('ld a,$3c')
    e.jr('font_hi_ready')
    e.label('font_hi_override')
    e.address('ld a,($0000)',9)
    e.label('font_hi_ready')
    e.op('cp $3c')
    e.jr('font_private','nz')
    e.address('ld a,($0000)',8)
    e.op('or a')
    e.jr('font_private','nz')
    e.op('ld hl,$3c00; ld ($5c36),hl; ret')
    e.label('font_private')
    e.address('ld hl,($0000)',11)
    e.op('ld ($5c36),hl; ret')


def _font_address_alias(e, base, total, action, font_alias=None):
    """Translate virtual CHARS glyph address to the process-owned glyph bank.

    The private font is selected by the SSX startup entry, not by a pointer
    supplied by BASIC. If the program has not selected a virtual font or
    the SSX does not carry a private bank, fall through to memory protection.
    """
    if action not in ('peek','poke'):
        raise ValueError('invalid font action')
    e.op('push bc; push de; push hl')
    if font_alias is None:
        e.address('ld a,($0000)',10)
        e.op('or a')
        e.jr('font_nomap', 'z')
        e.address('ld de,($0000)',8)
    else:
        e.op(f'ld de,${font_alias:04x}')
    e.op('or a; sbc hl,de')
    e.jr('font_nomap', 'c')
    e.op('ld a,h; cp 4')
    e.jr('font_nomap', 'nc')
    _cache_font_pointer(e,'alias')
    e.address('ld de,($0000)',11)
    e.op('ld a,d; cp $5d')
    e.jr('font_nomap', 'c')
    e.op('add hl,de')
    _process_address_check(e, base, total, 'font_mapped', 'font')
    e.label('font_mapped')
    e.op('pop de; pop de; pop bc')
    if action == 'peek':
        e.op('ld l,(hl); ld h,0; ret')
    else:
        e.op('ld (hl),e; ret')
    e.label('font_nomap')
    e.op('pop hl; pop de; pop bc')


def _native_peek(asm, base, load, total=0, font_alias=None, entry=0,
                 *, with_source=False):
    e = _Code(asm)
    e.op('ld a,h; cp $5c')
    e.jr('ordinary_trampoline','nz')
    e.op('ld a,l; cp $36')
    e.jp('chars0','z')
    e.op('cp $37')
    e.jp('chars1','z')
    e.op('cp $04')
    e.jr('kbd_trampoline','z')
    e.op('cp $39')
    e.jp('pip','z')
    e.op('cp $6a')
    e.jp('flags','z')
    e.op('cp $8c')
    e.jp('scr_ct','z')
    e.op('cp $78')
    e.jp('ordinary_bridge','c')
    e.op('cp $7b')
    e.jp('ordinary_bridge','nc')
    e.jr('after_trampolines')
    e.label('ordinary_trampoline')
    e.jp('ordinary_bridge')
    e.label('kbd_trampoline')
    e.jr('kstate')
    e.label('after_trampolines')
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
    e.label('chars0')
    e.address('ld a,($0000)',8)
    e.jr('result')
    e.label('chars1')
    e.address('ld a,($0000)',10)
    e.op('or a')
    e.jr('read_chars_hi','nz')
    e.op('ld a,$3c')
    e.jr('result')
    e.label('read_chars_hi')
    e.address('ld a,($0000)',9)
    e.jr('result')
    e.label('pip')
    e.address('ld a,($0000)',1)
    e.jr('result')
    e.label('flags')
    e.address('ld a,($0000)',0)
    e.jr('result')
    e.label('scr_ct')
    e.address('ld a,($0000)',12)
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
    _font_address_alias(e, base, total, 'peek', font_alias)
    # ROM and bitmap/attribute reads are public; other addresses must be
    # inside the process's compiler-allocated image/BSS, never ZX-UX globals.
    e.op('ld a,h; cp $5b')
    e.jr('read_public','c')
    _process_address_check(e, base, total, 'read_public')
    e.label('read_public')
    e.op('ld l,(hl); ld h,0; ret')
    raw = e.build(base, load, entry)
    if with_source:
        return raw, e.assembly(base, entry), tuple(sorted(
            [position for position, _ in e.absrefs] +
            [position for position, _ in e.absjumps]))
    return raw


def _native_poke(asm, base, load, total=0, font_alias=None, entry=0,
                 *, with_source=False):
    e = _Code(asm)
    e.op('ld a,h; cp $5c')
    e.jr('poke_trampoline','nz')
    e.op('ld a,l; cp $36')
    e.jp('chars0','z')
    e.op('cp $37')
    e.jp('chars1','z')
    e.op('cp $39')
    e.jr('pip','z')
    e.op('cp $6a')
    e.jr('flags','z')
    e.op('cp $8c')
    e.jp('scr_ct','z')
    e.op('cp $78')
    e.jr('ordinary','c')
    e.op('cp $7b')
    e.jr('ordinary','nc')
    e.jr('poke_after_trampoline')
    e.label('poke_trampoline')
    e.jr('ordinary')
    e.label('poke_after_trampoline')
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
    e.label('scr_ct')
    e.op('ld a,e')
    e.address('ld ($0000),a',12)
    e.op('ret')
    e.label('ordinary')
    _font_address_alias(e, base, total, 'poke', font_alias)
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
    _native_error_exit(e)
    e.label('chars0')
    e.op('ld a,e')
    e.address('ld ($0000),a',8)
    e.jr('chars_sync')
    e.label('chars1')
    e.op('ld a,e')
    e.address('ld ($0000),a',9)
    e.op('ld a,1')
    e.address('ld ($0000),a',10)
    e.label('chars_sync')
    _select_print_font(e)
    raw = e.build(base, load, entry)
    if with_source:
        return raw, e.assembly(base, entry), tuple(sorted(
            [position for position, _ in e.absrefs] +
            [position for position, _ in e.absjumps]))
    return raw


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
                emitted = fn(asm, self._zxux_sysvar_base, code_base, self._zxux_total,
                             getattr(self, '_zxux_font_alias', None), pc)
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
        from spectrum_fonts import detect_font_bank
        import source
        alias, has_poke = detect_font_bank(self.lines, source.Keywords(self.rom).TOKEN)
        self.m._zxux_font_alias = alias

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

"""Virtualize two archived games' Spectrum FRAMES reset in private storage.

The ZX Spectrum increments the FRAMES counter at 23672..23674. Motocross and
Buzzy Bee set its three bytes to 255, then read all three to time a game.
Native ZX-UX code must never write those shared addresses. Instead, record
an offset in process-owned BSS and read (real_ticks - reset_ticks - 1) modulo
2**24. Both the code generation and memory permission review require the
same exact original write/read patterns. Other POKE/PEEK behavior is unchanged.
"""
from __future__ import annotations
import re
from udg_bounds import _line_text

_TOKEN_NAMES = {0xf4: 'POKE', 0xbe: 'PEEK', 0xf1: 'LET', 0xea: 'REM', 0xba: 'INT'}
_SETUP = 'POKE23674,255:POKE23673,255:POKE23672,255'
_TIMER_READS = {2000: '/48', 1503: '/49'}
_BYTE_OP = re.compile(r'\b(?:POKE|PEEK)2367[234]\b')
_POKE_ADDRESS = re.compile(rb'^\s*(23672|23673|23674)\x0e.{5}\s*,\s*255\x0e.{5}', re.S)
_PEEK_ADDRESS = re.compile(rb'^\s*(23672|23673|23674)\x0e.{5}', re.S)


def timer_shape(lines):
    seen = {n: re.sub(r'\s+', '', _line_text(body, _TOKEN_NAMES)).upper()
            for n, body in lines}
    if len(seen) != len(lines):
        return None
    matches = []
    for setup, read, divisor in ((25, 2000, 48), (50, 1503, 49)):
        if seen.get(setup) != _SETUP:
            continue
        value = seen.get(read, '')
        read_expr = '65536*PEEK23674+256*PEEK23673+PEEK23672'
        if read_expr not in value or '/'+str(divisor) not in value:
            continue
        if (divisor == 48 and not value.startswith('LETT1=(')) or (divisor == 49 and not value.startswith('LETTIME=INT(')):
            continue
        matches.append((setup, read))
    if len(matches) != 1:
        return None
    setup, read = matches[0]
    if any(_BYTE_OP.findall(t) and n not in (setup, read)
           for n, t in seen.items()):
        return None
    if len(_BYTE_OP.findall(seen[setup])) != 3 or len(_BYTE_OP.findall(seen[read])) != 3:
        return None
    return setup, read


def allow_virtual_frame_clock(lines, findings):
    """Accept only accesses which the native compiler redirects to BSS."""
    shape = timer_shape(lines)
    if shape is None:
        return 0
    setup, read = shape
    accepted = 0
    used = set()
    for item in findings:
        if item.severity != 'block':
            continue
        if (item.line == setup and item.operation == 'POKE'
                and item.classification == 'global_memory_write'):
            m = re.fullmatch(r'\s*(23672|23673|23674)\s*,\s*255\s*', item.expression)
            if m:
                used.add(('write', int(m[1])))
            else:
                continue
        elif (item.line == read and item.operation == 'PEEK'
              and item.classification == 'global_memory_read'):
            m = re.match(r'^\s*(23672|23673|23674)\b', item.expression)
            if m:
                used.add(('read', int(m[1])))
            else:
                continue
        else:
            continue
        item.severity = 'info'
        item.classification = 'process_frame_clock'
        accepted += 1
    # Refuse partial review exemptions. Restore their exact original labels.
    complete = {(kind, addr) for kind in ('write', 'read')
                for addr in (23672, 23673, 23674)}
    if used != complete or accepted != 6:
        for item in findings:
            if item.classification == 'process_frame_clock':
                item.classification = ('global_memory_write' if item.operation == 'POKE'
                                       else 'global_memory_read')
                item.severity = 'block'
        return 0
    return accepted


def install(compiler):
    cls = compiler.Compiler
    if getattr(cls, '_zxux_frame_clock_installed', False):
        return
    old_reset = cls.reset
    old_layout = cls.layout_vars
    old_poke = cls.st_poke
    old_peek = cls.fn_peek

    def reset(self, program):
        old_reset(self, program)
        self._zxux_frame_shape = timer_shape(self.lines)
        self._zxux_frame_base = 0

    def layout_vars(self):
        old_layout(self)
        if self._zxux_frame_shape is not None:
            self._zxux_frame_base = self.pc
            self.pc = (self.pc + 3) & 0xffff

    def st_poke(self):
        if self._zxux_frame_shape and self.line_no == self._zxux_frame_shape[0]:
            m = _POKE_ADDRESS.match(bytes(self.buf[self.ch:]))
            if m:
                addr = int(m[1])
                self.number_to_hl()
                self.next_char()
                n = self.number_to_hl()
                if n != 255:
                    self.not_supported('timer reset value')
                if addr == 23672:
                    # Copy current ticks, never write the system FRAMES bytes.
                    self.emit('ld hl,($5C78)')
                    self.emit_op_reloc('ld (nn),hl', self._zxux_frame_base)
                    self.emit('ld a,($5C7A)')
                    self.emit_op_reloc('ld (nn),a', self._zxux_frame_base + 2)
                return
        return old_poke(self)

    def fn_peek(self):
        if self._zxux_frame_shape and self.line_no == self._zxux_frame_shape[1]:
            m = _PEEK_ADDRESS.match(bytes(self.buf[self.ch:]))
            if m:
                addr = int(m[1])
                parsed = self.number_to_hl()
                if parsed != addr:
                    self.not_supported('timer byte address')
                # Low 16 bits: current - start - 1, including borrowed carry.
                self.emit('ld hl,($5C78)')
                self.emit_op_reloc('ld de,(nn)', self._zxux_frame_base)
                self.emit('scf; sbc hl,de; push hl; ld a,($5C7A); ld b,a')
                self.emit_op_reloc('ld a,(nn)', self._zxux_frame_base + 2)
                self.emit('ld e,a; ld a,b; sbc a,e; pop hl')
                if addr == 23672:
                    self.emit('ld h,0')
                elif addr == 23673:
                    self.emit('ld l,h; ld h,0')
                else:
                    self.emit('ld l,a; ld h,0')
                self.t = compiler.POSINT
                return
        return old_peek(self)

    cls.reset = reset
    cls.layout_vars = layout_vars
    cls.st_poke = st_poke
    cls.fn_peek = fn_peek
    cls._zxux_frame_clock_installed = True

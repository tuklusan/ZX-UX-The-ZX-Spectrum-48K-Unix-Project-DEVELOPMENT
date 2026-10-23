"""Compile proved changing-width Sinclair string arrays.

Sinclair DIM replaces the row width and clears the data. HiSoft v1.1
bakes the width into the compiler; for the bounded Tug of War sprites,
reserve the largest row size while updating the runtime width header.
Both indexed reads and assignments use that header to find each row.
Unrelated string arrays retain upstream behavior.
"""
from __future__ import annotations
import re
from udg_bounds import _line_text


_TOKENS = {0xe9: 'DIM', 0xfa: 'IF', 0xcb: 'THEN', 0xf1: 'LET'}
_DIM = re.compile(r'\bDIM\s+([ab])\$\s*\(\s*2\s*,\s*(\d+)\s*\)', re.I)
_EXPECTED = {
    2230: [('b', 4)], 2232: [('b', 2)],
    4230: [('a', 4)], 4232: [('a', 2)],
    7017: [('a', 6), ('b', 6)],
}


def _proven_layout(lines):
    actual = {}
    for n, body in lines:
        decoded = re.sub(r'\s+', ' ', _line_text(body, _TOKENS)).upper()
        matches = [(m[1].lower(), int(m[2])) for m in _DIM.finditer(decoded)]
        if matches:
            actual[n] = matches
        if re.search(r'\bDIM\s+[ab]\$', _DIM.sub('', decoded), re.I):
            return False
        if n in (2230, 2232):
            if not all(word in decoded for word in ('THEN DIM B$(', 'LET B$(1)', 'LET B$(2)')):
                return False
        if n in (4230, 4232):
            if not all(word in decoded for word in ('THEN DIM A$(', 'LET A$(1)', 'LET A$(2)')):
                return False
    return actual == _EXPECTED


def install(compiler):
    cls = compiler.Compiler
    if getattr(cls, '_zxux_width_dim_installed', False):
        return
    original_reset = cls.reset
    original_dimensions = cls._dim_sizes_set
    original_dim = cls.st_dim
    original_string = cls.string_var_value

    def reset(self, prog):
        original_reset(self, prog)
        self._zxux_width_dim = _proven_layout(self.lines)
        self._zxux_width_requested = None

    def dim_sizes_set(self, ent, last, first):
        if (self._zxux_width_dim and first == 2 and last in (2, 4, 6)
                and any(ent is self.strvars[compiler.letter(ord(ch))]
                        for ch in 'ab')):
            self._zxux_width_requested = last
            ent['first'], ent['last'] = 2, 6
            return
        return original_dimensions(self, ent, last, first)

    def st_dim(self):
        if (not self._zxux_width_dim or self.line_no not in _EXPECTED
                or chr(self.get_char()).lower() not in 'ab'
                or self.buf[self.ch + 1] != ord('$')):
            return original_dim(self)
        name = self.get_char()
        sv = self.strvars[compiler.letter(name)]
        self.next_char()
        self.next_char()
        sv['flags'] = 1
        self._zxux_width_requested = None
        self.dim_sizes(sv)
        requested = self._zxux_width_requested
        if requested not in (2, 4, 6):
            self.not_supported('string array width')
        self.t = compiler.STRING
        self.emit('ld hl,{}', requested)
        self.st_hl(sv['addr'])
        self.ld_hl(sv['addr'] + 2)
        self.ld_bc_abs(2 * requested - 1)
        self.emit('ld a,32')
        self.call_rt(compiler.RT.MEM_FILL)

    def string_var_value(self, sv):
        if (not self._zxux_width_dim
                or not any(sv is self.strvars[compiler.letter(ord(ch))]
                           for ch in 'ab') or not sv['first']):
            return original_string(self, sv)
        self.next_char()
        self.expr_int()
        self.ld_de(sv['addr'])
        self.call_rt(compiler.RT.STR_ARR_ELEM)
        self._strarr_tail()

    cls.reset = reset
    cls._dim_sizes_set = dim_sizes_set
    cls.st_dim = st_dim
    cls.string_var_value = string_var_value
    cls._zxux_width_dim_installed = True

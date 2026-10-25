"""Use HiSoft's semantic argument type for Spectrum USR, never token spelling.

String-valued USR asks the ROM for a UDG pointer. Only the numeric form
would execute machine code; reject it in every compiler pass. A POKE with a
string-USR address checks the actual 168-byte process-owned UDG allocation at
runtime before using the native protected-memory POKE service.
"""
from __future__ import annotations

from native_sysvars_rt import POKE_RT

# The check leaves the original address in HL and does not write to memory.
# On failure ROM error 11 terminates the Spectrum statement. This check is
# before the value is evaluated, so an invalid address has no side effects.
UDG_POKE_CHECK = (
    'push hl; ld de,($5c7b); or a; sbc hl,de; '
    'jr c,+12; ld a,h; or a; jr nz,+8; '
    'ld a,l; cp 168; jr nc,+3; '
    'pop hl; jr +16; '
    # Every failure releases the screen and exits with native status 11.
    # ROM RST 8 is intercepted by ZX-UX as a kernel panic.
    'ld hl,0; ld a,39; call $6003; '
    'ld hl,11; ld a,1; jp $6003'
)


def install(compiler):
    """Install *after* process PEEK/POKE service, before building subclasses.

    All calls still pass through the genuine HiSoft operand parser. In
    particular `USR VAL A$` is numeric, however dynamic its source text.
    """
    cls = compiler.Compiler
    if getattr(cls, '_zxux_typed_usr', False):
        return
    if not getattr(cls, '_zxux_sysvars', False):
        raise ValueError('typed USR requires installed native protected-memory POKE')

    def fn_usr(self):
        self.operand()
        if self.t != compiler.STRING:
            self.not_supported('numeric USR machine-code execution is prohibited')
        self._zxux_usr_string_in_address = True
        self.call_rt(compiler.RT.USR_UDG)
        self.t = compiler.POSINT

    def st_poke(self):
        # Calling fn_usr in the *address* expression sets the flag. Numeric
        # USR never reaches here. An unbounded arithmetic offset still has to
        # pass the range check for the process's actual UDG base.
        self._zxux_usr_string_in_address = False
        self.expr_int()
        guarded = self._zxux_usr_string_in_address
        self._zxux_usr_string_in_address = False
        if guarded:
            self.emit(UDG_POKE_CHECK)
        self.emit('push hl')
        self.next_char()
        self.expr_int()
        self.emit('ld e,l; pop hl')
        self.call_rt(POKE_RT)

    cls.fn_usr = fn_usr
    cls.st_poke = st_poke
    cls._zxux_typed_usr = True

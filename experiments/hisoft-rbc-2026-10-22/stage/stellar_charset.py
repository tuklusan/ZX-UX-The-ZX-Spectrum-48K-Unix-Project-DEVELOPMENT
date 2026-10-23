"""Use a scoped Spectrum CHARS view for the preserved Stellar Run screen probe.

Stellar Run temporarily changes the global CHARS pointer to UDG minus 256,
reads SCREEN$ once, then returns CHARS to the ROM font. Native ZX-UX must
not leave the shared font pointer modified while the process runs. Here the
two original pointer-write lines are replaced in the temporary compiler input
with inert REM, and the sole specialized SCREEN$ call saves CHARS on the user
stack, substitutes UDG-256 inside a short interrupt-closed region, calls the
original 48K ROM SCREEN$ routine, and restores CHARS before reopening interrupts.

This is a narrow native code-generation implementation of the original
screen-recognition semantics, not permission for general shared-memory POKEs.
Every original BASIC text and tape byte remains intact.
"""
from __future__ import annotations
import re
from udg_bounds import _line_text

_BEFORE={
  110:'LETI=CODESCREEN$(Y+1,X):IFITHENRETURN',
  120:'POKE23606,PEEK23675:POKE23607,PEEK23676-1',
  130:'LETI=CODESCREEN$(Y+1,X)+112',
  140:'POKE23606,0:POKE23607,60',
  150:'RETURN',
  2315:'GOSUB100:IFI>144THENGOTO4000',
}
_AFTER=dict(_BEFORE); _AFTER.update({120:'',140:''})
_TOKEN_NAMES={0xf1:'LET',0xaf:'CODE',0xaa:'SCREEN$',0xfa:'IF',0xcb:'THEN',
              0xfe:'RETURN',0xf4:'POKE',0xbe:'PEEK',0xed:'GO SUB',
              0xec:'GO TO',0xea:'REM'}
_SHARED=re.compile(r'(?:POKE|PEEK)236(?:06|07|75|76)\b')
_ENTRY=re.compile(r'\bGO(?:TO|SUB)(?:12[0-9]|13[0-9]|14[0-9])\b')


def _shape(rows, names, adapted):
    if len(dict(rows))!=len(rows):return False
    visible={n:re.sub(r'\s+','',_line_text(b,names)).upper() for n,b in rows}
    required=_AFTER if adapted else _BEFORE
    if any(visible.get(n)!=t for n,t in required.items()):return False
    if any(_SHARED.search(t) for n,t in visible.items()
           if n not in (() if adapted else (120,140))):
        return False
    if any(_ENTRY.search(t) for t in visible.values()):
        return False
    # A second screen matching command on the same source line is not covered.
    if visible[130].count('SCREEN$')!=1:return False
    return True


def adapt_stellar_charset(program,kw,fp,source,tap):
    rows=list(tap.split_lines(program))
    if not _shape(rows,kw.TOKEN,False):return program,[]
    rem=bytes((kw.CODE_FOR['REM'],))+b'\r'
    rewritten=[(n,rem if n in (120,140) else b) for n,b in rows]
    if not _shape(rewritten,kw.TOKEN,True):return program,[]
    return tap.join_lines(rewritten),[{'source_lines':[120,130,140],
        'native_screen_line':130,'font_pointer':'CHARS 23606/23607',
        'temporary_charset':'UDG pointer 23675/23676 minus 256',
        'restore_before_return':True}]


def install(compiler):
    cls=compiler.Compiler
    if getattr(cls,'_zxux_stellar_charset_installed',False):return
    old_reset=cls.reset
    old_screen=cls.fn_screen

    def reset(self,program):
        old_reset(self,program)
        self._zxux_stellar_screen=_shape(self.lines,_TOKEN_NAMES,True)

    def screen(self):
        if self._zxux_stellar_screen and self.line_no==130:
            # The original SCREEN$ operands are compiled normally first.
            self.next_char()
            self.two_ints_bc()
            self.next_char()
            # No other task can see the temporarily changed shared CHARS.
            # The 48K ROM SCREEN$ call and the stack save/restore are balanced.
            self.emit('di; ld hl,($5C36); push hl; ld hl,($5C7B); dec h; ld ($5C36),hl')
            self._string_result(compiler.ROM['SCREEN'])
            self.emit('pop hl; ld ($5C36),hl; ei')
            return
        return old_screen(self)

    cls.reset=reset
    cls.fn_screen=screen
    cls._zxux_stellar_charset_installed=True


"""Recognize Stellar Run's bounded DATA-sourced UDG initialization.

The nine literal DATA rows define characters a..i, each with eight bytes in
0..255. The single initialization executes FOR a=1..9 / FOR b=0..7 and
POKE USR a$+b,c, with a$ read from the next corresponding DATA row. Every
address is within the program's process-owned Spectrum UDG area. Reject other
POKE, DATA, RESTORE and array/loop shapes; never allow a general USR pointer.
"""
from __future__ import annotations
import re
from udg_bounds import _line_text

_DATA={
  8010:'DATA"a",66,102,126,126,60,60,24,24',
  8020:'DATA"b",255,170,251,170,255,170,255,170',
  8030:'DATA"c",24,36,102,153,153,102,36,24',
  8040:'DATA"d",129,66,36,24,24,36,66,129',
  8050:'DATA"e",66,102,126,126,60,60,90,0',
  8060:'DATA"f",66,102,126,126,60,188,0,73',
  8070:'DATA"g",66,102,126,126,60,0,0,129',
  8080:'DATA"h",66,102,126,0,161,0,8,0',
  8090:'DATA"i",128,16,0,4,64,0,4,0',
}
_DATA={line:body.upper() for line,body in _DATA.items()}
_LOOP='FORA=1TO9:READA$:FORB=0TO7:READC:POKEUSRA$+B,C:NEXTB:NEXTA'
_ADDR = re.compile(r'^\s*USR\s+A\$\s*\+\s*B\s*,\s*C\s*$',re.I)
_USR = re.compile(r'^\s*(?:USR\s*)?A\$\s*\+\s*B(?:\s*,\s*C)?\s*$',re.I)


def _proved(rows,token_names):
    if len(dict(rows))!=len(rows):return False
    visible={n:re.sub(r'\s+','',_line_text(b,token_names)).upper() for n,b in rows}
    if any(visible.get(n)!=v for n,v in _DATA.items()):return False
    if visible.get(8100)!=_LOOP:return False
    # First DATA available at entry; no dynamic RESTORE may redirect reads.
    if any('RESTORE' in t for t in visible.values()):return False
    if {n for n,t in visible.items() if t.startswith('DATA')} != set(_DATA):
        return False
    if {n for n,t in visible.items() if 'POKE' in t} != {8100}:
        return False
    if 'GOSUB8000' not in visible.get(2,''):
        return False
    if any(re.search(r'\bGO(?:TO|SUB)(?:80[1-9][0-9]|8100)\b',t)
           for t in visible.values()):
        return False
    return True


def allow_literal_data_udgs(lines,token_names,findings):
    """Approve only one matching DATA-bound write and its associated USR."""
    rows=list(lines)
    if not _proved(rows,token_names):return 0
    writes=[f for f in findings if f.line==8100 and f.operation=='POKE' and
            f.classification=='unbounded_memory_write' and f.severity=='block']
    pointers=[f for f in findings if f.line==8100 and f.operation=='USR' and
              f.classification=='raw_machine_code_address' and f.severity=='block']
    if len(writes)!=1 or not _ADDR.fullmatch(writes[0].expression):return 0
    if len(pointers)!=1 or not _USR.fullmatch(pointers[0].expression):return 0
    writes[0].severity='info';writes[0].classification='bounded_data_udg_write'
    pointers[0].severity='info';pointers[0].classification='process_udg_pointer'
    return 2
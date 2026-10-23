"""Drop only consecutive identical literal FOR initializers.

Spectrum BASIC replaces the prior control frame when FOR reuses a variable.
When the second FOR is identical and immediately follows the first,
keeping only the second is equivalent and avoids the HiSoft nesting error.
"""
from __future__ import annotations
import re
from udg_bounds import _line_text

_FOR = re.compile(r'^\s*FOR\s+([a-z])\s*=\s*(\d+)\s*TO\s*(\d+)\s*$',re.I)
_REM = 0xEA


def remove_duplicate_for(program, kw, tap):
    rows=list(tap.split_lines(program))
    decoded=[(n,_line_text(body,kw.TOKEN)) for n,body in rows]
    removed={};details=[]
    for i in range(1,len(rows)):
        previous=_FOR.fullmatch(decoded[i-1][1]); current=_FOR.fullmatch(decoded[i][1])
        if previous is None or current is None:
            continue
        if tuple(x.lower() for x in previous.groups()) != tuple(x.lower() for x in current.groups()):
            continue
        # The first line does nothing except set the same loop state again.
        # Retain the line number so branch targets remain defined.
        before=rows[i-1][1]
        if not before.endswith(b'\r'):
            continue
        removed[rows[i-1][0]]=bytes((_REM,))+b'\r'
        details.append((rows[i-1][0],rows[i][0],previous[1].lower()))
    if not removed:
        return program,[]
    return tap.join_lines([(n,removed.get(n,body)) for n,body in rows]),details
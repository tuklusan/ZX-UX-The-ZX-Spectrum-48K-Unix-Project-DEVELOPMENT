"""Flatten proved Spectrum string arrays with three or four dimensions.

The original Swordsman arrays use row-major string records. Each record's
character width remains unchanged. All indexed sites and index-setting loops
are checked before converting the compiler's temporary tokenized copy.
"""
from __future__ import annotations
import re


_REFERENCES = {500: [b'D', b'M'], 510: [b'D'], 660: [b'M'],
               4038: [b'D'], 4060: [b'M'], 4088: [b'M']}
_WRITERS = {
    b'D7': {4010: 1, 4025: 1, 4030: 1, 4035: 2, 4036: 1, 4082: 1},
    b'M6': {4010: 1, 4089: 1},
    b'M7': {4010: 1, 4085: 2},
    b'MZ': {25: 1, 2960: 1},
}


def adapt_flat_string_dims(program, kw, fp, source, tap):
    rows = list(tap.split_lines(program))
    by = dict(rows)
    if len(rows) != len(by) or not _REFERENCES.keys() <= by.keys():
        return program, []
    n = lambda x: source.hide_numbers(str(x).encode('ascii'), fp)
    dim = bytes((kw.CODE_FOR['DIM'],))
    decl = (dim+b'D$('+n(4)+b','+n(3)+b','+n(4)+b'):'
            +dim+b'M$('+n(9)+b','+n(4)+b','+n(3)+b','+n(5)+b')\r')
    if by[500].upper() != decl.upper():
        return program, []
    seen={number: re.findall(rb'([DM])\$\(',body,re.I)
          for number,body in rows}
    seen={number:items for number,items in seen.items() if items}
    if seen != _REFERENCES:
        return program, []
    for var, expected in _WRITERS.items():
        writes={number: len(re.findall(bytes((kw.CODE_FOR['LET'],))+var+b'=',body,re.I))
                for number,body in rows}
        if {num:count for num,count in writes.items() if count} != expected:
            return program, []
    # Fixed bounded iterations and repeatable controls: no index can reach
    # an invalid component while any rewritten record is accessed.
    tests = {
        510: bytes((kw.CODE_FOR['FOR'],))+b'I='+n(1)+bytes((kw.CODE_FOR['TO'],))+n(4)
             +b':'+bytes((kw.CODE_FOR['FOR'],))+b'J='+n(1)
             +bytes((kw.CODE_FOR['TO'],))+n(3)+b':',
        650: bytes((kw.CODE_FOR['FOR'],))+b'K='+n(1)+bytes((kw.CODE_FOR['TO'],))+n(9)
             +b':'+bytes((kw.CODE_FOR['FOR'],))+b'J='+n(1)
             +bytes((kw.CODE_FOR['TO'],))+n(4)+b':'
             +bytes((kw.CODE_FOR['FOR'],))+b'I='+n(1)+bytes((kw.CODE_FOR['TO'],))+n(3)+b'\r',
        4038: bytes((kw.CODE_FOR['FOR'],))+b'X='+n(0)+bytes((kw.CODE_FOR['TO'],))+n(2)+b':',
        4060: bytes((kw.CODE_FOR['FOR'],))+b'X='+n(0)+bytes((kw.CODE_FOR['TO'],))+n(2)+b':',
        4088: bytes((kw.CODE_FOR['FOR'],))+b'X='+n(0)+bytes((kw.CODE_FOR['TO'],))+n(2)+b':',
    }
    if any(not by.get(line,b'').startswith(prefix) for line,prefix in tests.items()):
        return program, []
    # These fixed assignments supply the remaining live index ranges.
    if not (by[2960].startswith(bytes((kw.CODE_FOR['LET'],))+b'MZ='+bytes((kw.CODE_FOR['INT'],))+
                                  b'('+bytes((kw.CODE_FOR['RND'],))+b'*'+n(9)+b')+'+n(1))
            and bytes((kw.CODE_FOR['LET'],))+b'M6='+n(4) in by[4010]
            and bytes((kw.CODE_FOR['LET'],))+b'M6=M7' in by[4089]
            and bytes((kw.CODE_FOR['LET'],))+b'M7=M7+'+n(1) in by[4085]
            and bytes((kw.CODE_FOR['IF'],))+b'M7='+n(5) in by[4085]
            and bytes((kw.CODE_FOR['LET'],))+b'M7='+n(1) in by[4085]):
        return program, []
    # D7 is set only from the bounded movement directions of the game.
    for number, value in ((4010,2),(4025,1),(4030,2),(4035,4),(4036,3),(4082,2)):
        if bytes((kw.CODE_FOR['LET'],))+b'D7='+n(value) not in by[number]:
            return program, []
    old = {
        510: (b'D$(I,J)', b'D$((I-'+n(1)+b')*'+n(3)+b'+J)'),
        660: (b'M$(K,J,I)', b'M$((K-'+n(1)+b')*'+n(12)+b'+(J-'+n(1)+b')*'+n(3)+b'+I)'),
        4038: (b'D$(D7,X+'+n(1)+b')', b'D$((D7-'+n(1)+b')*'+n(3)+b'+X+'+n(1)+b')'),
        4060: (b'M$(MZ,M6,X+'+n(1)+b')', b'M$((MZ-'+n(1)+b')*'+n(12)
               +b'+(M6-'+n(1)+b')*'+n(3)+b'+X+'+n(1)+b')'),
        4088: (b'M$(MZ,M6,X+'+n(1)+b')', b'M$((MZ-'+n(1)+b')*'+n(12)
               +b'+(M6-'+n(1)+b')*'+n(3)+b'+X+'+n(1)+b')'),
    }
    changed = {500: dim+b'D$('+n(12)+b','+n(4)+b'):'
                     +dim+b'M$('+n(108)+b','+n(5)+b')\r'}
    for number,(original,replacement) in old.items():
        if by[number].count(original) != 1:
            return program, []
        changed[number] = by[number].replace(original, replacement, 1)
    return tap.join_lines([(line,changed.get(line,body)) for line,body in rows]), [
        {'line':500, 'array_shapes':{'D$':[12,4], 'M$':[108,5]},
         'rewritten_accesses':5}]

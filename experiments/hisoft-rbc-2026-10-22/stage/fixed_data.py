"""Compile DATA scalar expressions only under a fully checked value proof.

Sinclair BASIC resolves DATA expressions when READ consumes the field. This
pass changes a scalar-valued DATA field to a literal only where the variable
has the same known value on every reachable READ of the target DATA line.
Any different structure is left for genuine runtime DATA expression support.
"""
from __future__ import annotations

import re
from constant_data import _separate
from udg_bounds import _line_text

_DATA = 0xE4


def specialize_fixed_data(program, kw, fp, source, tap):
    rows=list(tap.split_lines(program))
    body_by_line=dict(rows)
    text={n:_line_text(body,kw.TOKEN) for n,body in rows}
    # Strict 48K race-loop proof. The glyph-building FOR changes l; its
    # successor resets l before entering the actual car simulation.
    required={
        15: r'GO\s+SUB\s+9000',
        9300: r'FOR\s+l\s*=\s*1\s+TO\s+26.*\bNEXT\s+l\b',
        9350: r'^\s*RESTORE\s+9400\s*$',
        9370: r'^\s*LET\s+l\s*=\s*-1\s*$',
        160: r'READ\s+q\b',
        165: r'RESTORE\s+9400',
        9600: r'^\s*RETURN\s*$',
    }
    if any(n not in text or re.search(pattern,text[n],re.I) is None
           for n,pattern in required.items()):
        return program, []
    if not (9300<9350<9370<9400<9600):
        return program, []
    # Both uses of RESTORE 9400 are known, and l has only the initializer
    # and the earlier graphic setup as writers. Do not infer other flows.
    for n,t in text.items():
        if re.search(r'\bRESTORE\s+9400\b',t,re.I) and n not in (165,9350):
            return program, []
        if re.search(r'\b(?:LET|FOR|READ|INPUT)\s+l\b',t,re.I) and n not in (9300,9370):
            return program, []
        if n!=9300 and re.search(r'\bNEXT\s+l\b',t,re.I):
            return program, []
        # Branches into the initializer/data body or starting at the race
        # loop would invalidate the straight-line-before-READ proof.
        for match in re.finditer(r'\bGO\s*(?:TO|SUB)\s+(\d+)\b',t,re.I):
            dest=int(match[1])
            if 9300<dest<=9400:
                return program, []
    body=body_by_line[9400]
    if body[:1]!=bytes((_DATA,)) or not body.endswith(b'\r') or body.count(bytes((_DATA,)))!=1:
        return program, []
    fields=_separate(body[1:-1])
    if len(fields)!=26:
        return program, []
    changed=[];count=0
    for field in fields:
        stripped=field.strip().lower()
        if stripped in (b'l',b'-l'):
            # Keep Sinclair's unary minus separate from the numeric token.
            constant=(b'-' if stripped==b'l' else b'')+source.hide_numbers(b'1',fp)
            prefix=field[:len(field)-len(field.lstrip())]
            suffix=field[len(field.rstrip()):]
            changed.append(prefix+constant+suffix)
            count+=1
        elif re.fullmatch(rb'-?[0-9]+(?:\x0e.{5})?',stripped,re.S):
            changed.append(field)
        else:
            return program, []
    if count<1:
        return program, []
    out=[(n,(bytes((_DATA,))+b','.join(changed)+b'\r') if n==9400 else b)
         for n,b in rows]
    return tap.join_lines(out),[{'line':9400,'fields':len(fields),'fixed_fields':count,'value':-1}]
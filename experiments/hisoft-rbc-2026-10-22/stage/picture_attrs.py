"""Prove and guard Picture Pairs' seven native screen-attribute writes.

The original BASIC draws its 20 picture backs via screen attributes at
22595+T(slot)+U(offset). With the published DATA these are the character
attribute bytes 22595..23161, all inside 22528..23295. This is video RAM,
not the process or kernel's general memory.

The preserved second-guess condition at line 330 tests X>20, not P>20.
On a bad index the 48K BASIC interpreter would report a subscript error;
this native transformation adds an explicit STOP for P>20 before any array
access. Both original BASIC input files remain unchanged.

This is an exact-shape-checked exception for provably bounded display cells.
No other memory writes gain approval; changing a DATA value, array writer,
control branch, or address expression invalidates the entire proof.
"""
from __future__ import annotations
import re
from udg_bounds import _line_text

_REQUIRED = {
  30:'DIMA(12,72):DIMQ(20):DIMR(20):DIMT(20):DIMU(20)',
  200:'LETW=57+INT(RND*3):LETZ=22595',
  210:'FORX=1TO9:FORY=1TO20:POKEZ+T(Y)+U(X),W:NEXTY:NEXTX',
  250:'LETW=18:LETZ=22595',
  260:'FORX=1TO20:FORY=1TO9:POKEZ+T(X)+U(Y),W:NEXTY:NEXTX',
  300:'IFP<1ORP>20THENGOTO270',
  305:'LETQ=P:LETSA=P',
  307:'FORX=1TO9:POKEZ+T(P)+U(X),40:NEXTX',
  330:'GOSUB540:IFP<1ORX>20THENGOTO310',
  335:'FORX=1TO9:POKEZ+T(P)+U(X),40:NEXTX',
  520:'FORX=1TO9:POKEZ+T(Q)+U(X),V:NEXTX:FORX=1TO9:POKEZ+T(P)+U(X),V:NEXTX:RETURN',
  530:'FORX=1TO9:POKEZ+T(P)+U(X),57:NEXTX:RETURN',
  560:'LETP=5*(A-6)+B',
  610:'FORX=1TO11:FORY=1TO72:READA(X,Y):NEXTY:NEXTX',
  620:'FORX=1TO20:READQ(X):NEXTX:FORX=1TO20:READR(X):NEXTX',
  630:'FORX=1TO20:READT(X):NEXTX:FORX=1TO9:READU(X):NEXTX',
  2040:'DATA0,5,10,15,20,160,165,170,175,180,320,325,330,335,340,480,485,490,495,500',
  2050:'DATA0,1,2,32,33,34,64,65,66',
}
_ATTR_LINES = (210,260,307,335,520,530)
_POKE_EXPECTED={210:1,260:1,307:1,335:1,520:2,530:1}
_BOUNDED = {'210':('Y','X','W'), '260':('X','Y','W'),
            '307':('P','X','40'), '335':('P','X','40'),
            '520':None, '530':('P','X','57')}
_GUARD = ':IFP>20THENSTOP'


def _normalized(rows, kw):
    return {n:re.sub(r'\s+','',_line_text(b,kw.TOKEN)).upper()
            for n,b in rows}


def _prove(rows, kw, guarded):
    bodies=dict(rows)
    if len(bodies)!=len(rows):
        return False
    t=_normalized(rows,kw)
    expected=dict(_REQUIRED)
    if guarded:
        expected[330] += _GUARD
    if any(t.get(n)!=v for n,v in expected.items()):
        return False
    # Rejections are intentional: no hidden alternate source of array data,
    # display pointer, index, or state entering this exact data/paint protocol.
    if any('RESTORE' in line for line in t.values()):
        return False
    if {n for n,line in t.items() if 'POKE' in line} != {15,70,*_ATTR_LINES}:
        return False
    for n,line in t.items():
        if 'POKE' in line and line.count('POKE') != ({15:1,70:1,**_POKE_EXPECTED}.get(n,0)):
            return False
        if n not in (200,250) and re.search(r'\bLETZ\s*=',line):
            return False
        if n!=560 and re.search(r'\bLETP\s*=',line):
            return False
        if n!=305 and re.search(r'\bLETQ\s*=',line):
            return False
        if re.search(r'\b(?:LET|INPUT|READ)\s*[TU]\s*\(',line):
            if n!=630:
                return False
        if n!=630 and re.search(r'\bREAD\s*[TU]\s*\(',line):
            return False
        if n!=30 and re.search(r'\bDIM\s*[TU]\s*\(',line):
            return False
    # Do not accept arbitrary jumps into the second-pick handler between its
    # input validation and the first write. Only the native guarded entry works.
    if any(re.search(r'\b(?:GOTO|GOSUB)(?:33[1-9]|34[0-9])\b',line)
           for line in t.values()):
        return False
    # Verify every original expression, including the two writes on line 520.
    for n in _ATTR_LINES:
        found=re.findall(r'POKEZ\+T\(([^)]*)\)\+U\(([^)]*)\),([A-Z0-9]+)',t[n])
        required={210:[('Y','X','W')],260:[('X','Y','W')],
                  307:[('P','X','40')],335:[('P','X','40')],
                  520:[('Q','X','V'),('P','X','V')],530:[('P','X','57')]}
        if found!=required[n]:
            return False
    # Value bounds of every written address, irrespective of screen layout.
    top=22595+max((0,5,10,15,20,160,165,170,175,180,
                   320,325,330,335,340,480,485,490,495,500))+66
    return 22528<=22595 and top<23296


def adapt_picture_attrs(program,kw,fp,source,tap):
    rows=list(tap.split_lines(program))
    if not _prove(rows,kw,False):
        return program,[]
    # Insert after the original branch. A legitimate P in 1..20 is untouched;
    # a larger P stops before S$(P), T(P), and later picture attributes.
    original=dict(rows)[330]
    if not original.endswith(b'\r'):
        return program,[]
    guard=(b':'+bytes((kw.CODE_FOR['IF'],))+b'P>'+source.hide_numbers(b'20',fp)
           +bytes((kw.CODE_FOR['THEN'],))+bytes((kw.CODE_FOR['STOP'],)))
    amended=original[:-1]+guard+b'\r'
    updated=[(n,amended if n==330 else b) for n,b in rows]
    if not _prove(updated,kw,True):
        return program,[]
    return tap.join_lines(updated),[{'guard_line':330,'attribute_write_lines':list(_ATTR_LINES),
                                    'attribute_write_count':7,'address_min':22595,
                                    'address_max':23161,'source_limits':'T(1..20) and U(1..9)',
                                    'invalid_second_index':'native STOP'}]


def allow_bounded_picture_attributes(lines, token_names, findings):
    """Grant only seven exact proven video-attribute POKEs, atomically."""
    class KW:
        TOKEN=token_names
    if not _prove(list(lines),KW(),True):
        return 0
    eligible=[x for x in findings if x.operation=='POKE' and
              x.classification=='unbounded_memory_write' and x.severity=='block'
              and x.line in _ATTR_LINES]
    if len(eligible)!=7 or any(
        len([x for x in eligible if x.line==n])!=_POKE_EXPECTED[n]
        for n in _ATTR_LINES):
        return 0
    valid=re.compile(r'^\s*Z\s*\+\s*T\s*\(\s*([XPQY])\s*\)\s*\+\s*U\s*\(\s*([XY])\s*\)\s*,\s*(W|V|40|57)\s*$',re.I)
    if any(not valid.fullmatch(x.expression) for x in eligible):
        return 0
    for finding in eligible:
        finding.classification='bounded_screen_attribute_write'
        finding.severity='info'
    return 7
"""Preserve a proved numeric-array reset when HiSoft rejects a smaller DIM.

A larger backing array is equivalent only if the omitted elements can never
be observed. In the preserved Wordsum game the later C(6) resets the first
six cells and only those cells are read; retaining its initial C(10) size
allows the original compiler to perform that reset. Other layouts are left
untouched for true dynamic/repeated-DIM support.
"""
from __future__ import annotations
import re
from udg_bounds import _line_text

# These original control and arithmetic statements prove the maximum observed
# subscript of C is six, even when another round resets it.
_REQUIRED = {
    40: 'DIMA(10):DIMC(10):DIMA$(10):DIMW$(60,6)',
    80: 'BORDER6:PAPER5:INK1:LETT=0:LETNN=1+INT(N*RND):LETX=6:IFW$(NN)(6)=""THENLETX=5',
    82: 'LETP$=W$(NN)(TOX)',
    90: 'FORX=1TOLENP$',
    120: 'FORZ=1TOX-1:IFA$(X)=A$(Z)THENLETA(X)=A(Z):GOTO190',
    140: 'LETA(X)=INT(RND*10)',
    150: 'IFA(1)=0THENGOTO140',
    190: 'NEXTX',
    200: 'LETP=0',
    210: 'FORX=LENP$TO1STEP-1',
    220: 'LETT=T+A(X)*10^P',
    230: 'LETP=P+1',
    240: 'NEXTX',
    270: 'LETS$=STR$S:LETT$=STR$T:LETI$=STR$I',
    280: 'FORX=1TOLENT$',
    320: 'IFI$(Y)=T$(X)THENLETC(X)=1:LETI$(Y)=A$(X)',
    350: 'NEXTX',
    440: 'FORX=1TOLENT$',
    450: 'IFC(X)=0THENLETT$(X)=A$(X)',
    460: 'NEXTX',
    586: 'DIMC(6):GOTO80',
}


def adapt_bounded_redim(program, kw, fp, source, tap):
    rows=list(tap.split_lines(program))
    bodies=dict(rows)
    if len(bodies)!=len(rows) or not _REQUIRED.keys() <= bodies.keys():
        return program, []
    texts={n:re.sub(r'\s+', '', _line_text(body, kw.TOKEN)).upper()
           for n,body in rows}
    if any(texts[n]!=expected for n,expected in _REQUIRED.items()):
        return program, []
    # No other indexed C or writes that could produce longer result digits.
    indices={n:re.findall(r'C\(([^)]*)\)',text)
             for n,text in texts.items()}
    if {n:v for n,v in indices.items() if v} != {
            40:['10'],320:['X'],450:['X'],586:['6']}:
        return program, []
    if any(('USR' in t or 'POKE' in t or 'CLEAR' in t)
           for t in texts.values()):
        return program, []
    if any(re.search(r'\b(?:INPUT|READ)\s+T\b',_line_text(b,kw.TOKEN),re.I)
           for _,b in rows):
        return program, []
    if any('LETT=' in t and n not in (80,220) or
           'LETA(' in t and n not in (120,140) or
           'LETT$=' in t and n!=270 or
           'LETP$=' in t and n!=82 or
           'LETP=' in t and n not in (200,230)
           for n,t in texts.items()):
        return program, []
    if any(280<n<350 and 'FORX=' in t or 440<n<460 and 'FORX=' in t
           for n,t in texts.items()):
        return program, []
    dim=kw.CODE_FOR['DIM']; goto=kw.CODE_FOR['GO TO']
    pattern=(bytes((dim,))+rb'\s*C\(6\x0e.{5}\):'
             +bytes((goto,))+rb'80\x0e.{5}\r')
    match=re.fullmatch(pattern,bodies[586],re.S|re.I)
    if match is None:
        return program, []
    amended=(bytes((dim,))+b'C('+source.hide_numbers(b'10',fp)+b'):'
             +bytes((goto,))+bodies[586].split(bytes((goto,)),1)[1])
    updated=[(n,amended if n==586 else b) for n,b in rows]
    return tap.join_lines(updated), [{'line':586,'array':'C',
                                     'initial_capacity':10,'observed_capacity':6}]

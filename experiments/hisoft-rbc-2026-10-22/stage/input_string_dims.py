"""Reserve proven string-input capacity for the Anagrammatic DIM expressions.

HiSoft native INPUT A$ uses its default fixed string width of 255 bytes.
The only assignment to L is LEN A$, so 1 <= L <= 255 at the DIM line.
The program uses B$ and C$ only as indexed characters and Q only with
subscripts within L. A 255-byte backing dimension therefore retains every
reachable character and number; the larger tails are unobservable.

This is a narrow, source-shape-checked compiler adaptation, not a general
claim that variable-sized DIM has been implemented. The BASIC remains intact.
"""
from __future__ import annotations

import re
from udg_bounds import _line_text

_CAPACITY = 255  # HiSoft compiler default_len=0xff for undimensioned INPUT A$.

_REQUIRED = {
    140: 'INPUTA$:IFA$=""THENGOTO140',
    160: 'LETL=LENA$',
    200: 'INPUTK$:LETW=L',
    210: 'LETT=0:FORJ=1TOLENK$:IFK$(J)="-"THENLETT=T+1',
    220: 'NEXTJ:IFT<>LTHENGOSUB1000:GOTO200',
    240: 'LETK$="":FORJ=1TOL:LETK$=K$+"-":NEXTJ',
    250: 'INPUT"NUMBEROFLETTERSTOBEGIN",W',
    260: 'IFW<1ORW>LORW<>INTWTHENGOSUB1000:GOTO250',
    270: 'DIMB$(L):DIMC$(L):DIMQ(L)',
    300: 'FORJ=WTOL',
    310: 'LETK=1',
    320: 'LETQ(K)=1',
    330: 'IFB$(Q(K))=""THENGOTO440',
    340: 'LETC$(K)=B$(Q(K)):LETB$(Q(K))=""',
    350: 'LETK=K+1',
    360: 'IFK<=JTHENGOTO320',
    370: 'LETA=1',
    380: 'FORS=1TOLENK$',
    390: 'IFK$(S)="-"THENPRINTC$(A);:LETA=A+1:GOTO410',
    410: 'NEXTS:PRINT',
    420: 'LETK=J',
    430: 'LETB$(Q(K))=A$(Q(K))',
    440: 'LETQ(K)=Q(K)+1',
    450: 'IFQ(K)<=LTHENGOTO330',
    460: 'LETK=K-1',
    470: 'IFK>=1THENGOTO430',
    480: 'NEXTJ',
    500: 'FORN=1TOL',
    510: 'LETB$(N)=A$(N):NEXTN:RETURN',
}

_ARRAY_ACCESS = re.compile(r'(?:B\$|C\$|Q)\s*\(', re.I)
_L_WRITE = re.compile(r'\b(?:LET|FOR|INPUT|READ)\s+L\s*(?:=|[,;:\r]|$)', re.I)


def adapt_input_string_dims(program, kw, fp, source, tap):
    rows = list(tap.split_lines(program))
    bodies = dict(rows)
    if len(bodies) != len(rows) or not _REQUIRED.keys() <= bodies.keys():
        return program, []
    texts = {n: re.sub(r'\s+', '', _line_text(body, kw.TOKEN)).upper()
             for n, body in rows}
    if any(texts.get(n) != expected for n, expected in _REQUIRED.items()):
        return program, []
    # Character tails must never be accessed via whole-string operations,
    # other indexes, or another DIM. Likewise, L cannot be reassigned.
    if {n for n, t in texts.items() if _ARRAY_ACCESS.search(t)} != {
            270, 320, 330, 340, 390, 430, 440, 450, 510}:
        return program, []
    if any('B$' in t or 'C$' in t for n, t in texts.items()
           if n not in {270, 330, 340, 390, 430, 510}):
        return program, []
    if any(_L_WRITE.search(_line_text(b, kw.TOKEN)) for n, b in rows if n != 160):
        return program, []
    # No machine-memory rewrite or unexpected flow may enter the DIM group.
    if any(re.search(r'\b(?:POKE|CLEAR|USR)\b', t) for t in texts.values()):
        return program, []
    # The DIM line must be precisely the three expected dimensions.
    dim = bytes((kw.CODE_FOR['DIM'],))
    pattern = (re.escape(dim) + rb'\s*B\$\(\s*L\s*\)\s*:\s*'
               + re.escape(dim) + rb'\s*C\$\(\s*L\s*\)\s*:\s*'
               + re.escape(dim) + rb'\s*Q\(\s*L\s*\)\s*\r')
    if re.fullmatch(pattern, bodies[270], re.I) is None:
        return program, []
    size = source.hide_numbers(str(_CAPACITY).encode('ascii'), fp)
    changed = (dim + b'B$(' + size + b'):' + dim + b'C$(' + size + b'):'
               + dim + b'Q(' + size + b')\r')
    updated = [(n, changed if n == 270 else b) for n, b in rows]
    return tap.join_lines(updated), [{
        'line': 270, 'arrays': ['B$', 'C$', 'Q'], 'capacity': _CAPACITY,
        'bound': 'LEN A$ (HiSoft INPUT string width)', 'input_line': 140,
    }]
"""Use a proved input upper bound for native fixed-size numeric arrays.

The original Postman inputs a number of boxes, rechecks it before the only
array initialization, and never assigns that value again. Allocating the
maximum 36 elements keeps every reachable original element and lets the
native compiler use its fixed-size DIM implementation. No original file is
edited; all other programs are left untouched.
"""
from __future__ import annotations
import re
from udg_bounds import _line_text


def adapt_input_bound_dims(program,kw,fp,source,tap):
    rows=list(tap.split_lines(program))
    bodies=dict(rows)
    if len(bodies)!=len(rows):
        return program,[]
    texts={n:re.sub(r'\s+','',_line_text(body,kw.TOKEN)).upper()
           for n,body in rows}
    required={
        10:'GOSUB5500', 20:'GOSUB7000',
        5003:'LETF=INT(RND*LB)+1',
        5790:'IFLB<1ORLB>36THENGOTO5780',
        5800:'RETURN',
        7060:'DIMY(LB):DIMX(LB)',
        7100:'FORF=1TOLB',
        7125:'LETY(F)=Y:LETX(F)=X',
        7850:'LETLET=0:LETPY=Y(LB):LETPX=X(LB)',
    }
    if any(texts.get(n)!=body for n,body in required.items()):
        return program,[]
    entry=texts.get(5500,'')
    if not re.fullmatch(r'INPUT"[^"\r]*";LB',entry):
        return program,[]
    if texts.get(8060,'')!='CLS:GOTO10':
        return program,[]
    # Exact originally observed indices: one or two reads/assignments per
    # field. No other Y() or X() could reach beyond the bounded allocation.
    observed={n:re.findall(r'[YX]\(([^)]*)\)',t) for n,t in texts.items()}
    observed={n:parts for n,parts in observed.items() if parts}
    if observed!={5010:['F','F','F','F'],5020:['F','F'],7060:['LB','LB'],
                  7125:['F','F'],7850:['LB','LB']}:
        return program,[]
    # Forbid reassigning the controlling input and any alternate entry to
    # its bound check or the DIM routine. The sole array initializer is the
    # numbered subroutine called from line 20 after the input subroutine.
    for n,t in texts.items():
        if n!=5500 and re.search(r'\b(?:INPUT|LET|READ|FOR)\s*LB\b',
                                 _line_text(bodies[n],kw.TOKEN),re.I):
            return program,[]
        if n!=20 and ('GOSUB7000' in t or 'GOTO7000' in t):
            return program,[]
        if re.search(r'GO(?:TO|SUB)(?:5500|5790|5800|7060|7100|7125)',t) and n!=10:
            return program,[]
        if 'GOTO5780' in t and n!=5790:
            return program,[]
    dim=kw.CODE_FOR['DIM']
    body=bodies[7060]
    pattern=(bytes((dim,))+rb'\s*[yY]\(lb\):'+bytes((dim,))+rb'\s*[xX]\(lb\)\r')
    if re.fullmatch(pattern,body,re.I|re.S) is None:
        return program,[]
    new=(bytes((dim,))+b'y('+source.hide_numbers(b'36',fp)+b'):'
         +bytes((dim,))+b'x('+source.hide_numbers(b'36',fp)+b')\r')
    amended=[(n,new if n==7060 else b) for n,b in rows]
    return tap.join_lines(amended),[{'line':7060,'arrays':['y','x'],
                                     'capacity':36,'bound_line':5790}]

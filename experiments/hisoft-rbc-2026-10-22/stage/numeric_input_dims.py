"""Bound two original numeric INPUT-dependent DIM statements in native memory.

The HiSoft compiler lays out numeric array storage at compile time. Until its
runtime allocator supports genuine changing sizes, reserve a bounded region,
then reject impossible native player counts BEFORE any indexed access. The
original control variables and all loops retain their runtime input values.

This is not unlimited DIM: counts beyond the configured capacity stop cleanly
on the native target. Such inputs remain fidelity gaps, not completed behavior.
Other original programs and the historical source/tape bytes are untouched.
"""
from __future__ import annotations
import re
from udg_bounds import _line_text

# Capacities are target-side reservations, not inferred source limits.
# They are deliberately modest for ZX-UX's available process RAM.
_SHAPES = {
    'horse': {
        'input': 3, 'dim': (4, 2030), 'capacity': 128, 'name': 'a',
        'required': {
            3: 'INPUT"HOWMANYPUNTERSARETHERE?",A',
            4: 'DIMP(A):FORC=1TOA',
            5: 'LETP(C)=200',
            6: 'NEXTC',
            1100: 'FORR=1TOA',
            2030: 'DIME(A):DIMB(A):FORF=1TOA',
            2040: 'NEXTF',
            6010: 'FORF=1TOA',
            6030: 'NEXTF',
        },
        'indices': {
            4: [('p','a')], 5: [('p','c')], 1101: [('p','r')],
            1105: [('e','r'),('p','r'),('p','r'),('b','r')],
            1110: [('p','r'),('p','r'),('b','r')], 1115: [('p','r')],
            1117: [('e','r')], 1120: [('p','r')], 1125: [('p','r')],
            2030: [('e','a'),('b','a')], 2031: [('p','f')],
            2032: [('p','f')], 2033: [('b','f'),('b','f'),('p','f')],
            2034: [('b','f'),('b','f')], 2036: [('e','f')],
            2037: [('e','f'),('e','f')], 6016: [('p','f')],
            6020: [('p','f')], 8030: [('p','r')], 8040: [('p','r')],
        },
    },
    'sheep': {
        'input': 30, 'dim': (40,), 'capacity': 255, 'name': 'A',
        'required': {
            30: 'INPUT"HOWMANYPLAYERS?";A',
            40: 'DIMP(A):DIMS(4,2):LETDX=15:LETDY=15:BORDER4:PAPER4:INK4:CLS',
            80: 'FORT=1TOA:',
            2010: 'FORX=1TOA',
            2020: 'PRINTTAB9;"PLAYER";X;"";P(X)',
            3002: 'LETP(T)=150-SC',
        },
        'indices': {
            40:[('p','a')], 2020:[('p','x')], 3002:[('p','t')],
            3040:[('p','t')], 3050:[('p','t')],
        },
    },
}

_READ_INDEX = re.compile(r'([PBE])\s*\(\s*([^)]*?)\s*\)', re.I)
_WRITE = re.compile(r'\b(?:LET|INPUT|READ|FOR)\s+A\s*(?:=|[,:;]|$)', re.I)


def _choose(texts):
    for name, shape in _SHAPES.items():
        if all(texts.get(n) == expected for n,expected in shape['required'].items()):
            return name, shape
    return None, None


def adapt_numeric_input_dims(program, kw, fp, source, tap):
    rows=list(tap.split_lines(program))
    bodies=dict(rows)
    if len(rows)!=len(bodies):
        return program, []
    texts={n:re.sub(r'\s+', '', _line_text(b, kw.TOKEN)).upper()
           for n,b in rows}
    name, shape=_choose(texts)
    if shape is None:
        return program, []
    wanted=shape['indices']
    indices={n:[(a.lower(),idx.lower()) for a,idx in _READ_INDEX.findall(t)]
             for n,t in texts.items()}
    indices={n:v for n,v in indices.items() if v}
    if indices != wanted:
        return program, []
    # The controlling INPUT is the only write to A; replacing the DIM
    # expression does not change FOR bounds or subsequent numeric references.
    for n,b in rows:
        if n!=shape['input'] and _WRITE.search(_line_text(b, kw.TOKEN)):
            return program, []
    dim=bytes((kw.CODE_FOR['DIM'],))
    size=source.hide_numbers(str(shape['capacity']).encode('ascii'),fp)
    changes={}
    for n in shape['dim']:
        body=bodies[n]
        if name=='horse' and n==4:
            pattern=rb'^'+re.escape(dim)+rb'\s*p\(\s*a\s*\)(?=:)'
            expected=1
        elif name=='horse':
            pattern=re.escape(dim)+rb'\s*[eb]\(\s*a\s*\)'
            expected=2
        else:
            pattern=rb'^'+re.escape(dim)+rb'\s*p\(\s*A\s*\)(?=:)'
            expected=1
        spans=list(re.finditer(pattern,body,re.I))
        if len(spans)!=expected:
            return program, []
        replacement=bytearray(body)
        for m in reversed(spans):
            fragment=body[m.start():m.end()]
            start=fragment.index(b'(')+1
            end=fragment.index(b')',start)
            replacement[m.start()+start:m.start()+end]=size
        changes[n]=bytes(replacement)
    # Add a native resource limit check directly after INPUT. The original
    # INPUT statement executes unmodified and the native count is retained.
    original=bodies[shape['input']]
    if not original.endswith(b'\r'):
        return program, []
    guard=(b':'+bytes((kw.CODE_FOR['IF'],))+b'A<'+source.hide_numbers(b'1',fp)
           +bytes((kw.CODE_FOR['OR'],))+b'A>'+size
           +bytes((kw.CODE_FOR['THEN'],))+bytes((kw.CODE_FOR['STOP'],)))
    changes[shape['input']]=original[:-1]+guard+b'\r'
    return tap.join_lines([(n,changes.get(n,b)) for n,b in rows]), [{
        'input_line':shape['input'], 'dim_lines':list(shape['dim']),
        'arrays':{'horse':['p','e','b'],'sheep':['p']}[name],
        'native_max_players':shape['capacity'],
        'larger_counts':'native STOP; original BASIC behavior not proven',
    }]
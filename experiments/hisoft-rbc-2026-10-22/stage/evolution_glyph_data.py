"""Compile the preserved Evolution 1's immediate literal glyph DATA transaction.

At line 1000 the archived source sets A=0 then RESTOREs line 1010 and
reads exactly 32 glyph bytes in one bounded FOR/READ/POKE/NEXT statement.
Four fields in those 32 DATA cells contain A. The original HiSoft compiler
accepts only numeric DATA literals; substituting these four proven zero
values in transient tokenized input retains their runtime values. No other
DATA transaction or original BASIC source byte is changed.
"""
from __future__ import annotations
import re
from udg_bounds import _line_text

_DATA = 0xE4
_START = 1010
_DATA_LINES = (1010, 1020, 1030, 1040)
_REQUIRED_START = 'LETA=0:RESTORE1010:FORF=USR"A"TOUSR"D"+7:READG:POKEF,G:NEXTF'


def _split_fields(data):
    fields=[];start=0;pos=0
    while pos<len(data):
        if data[pos]==14 and pos+5<len(data):
            pos+=6;continue
        if data[pos]==ord(','):
            fields.append(data[start:pos]);start=pos+1
        pos+=1
    fields.append(data[start:])
    return fields


def adapt_evolution_glyph_data(program,kw,fp,source,tap):
    lines=list(tap.split_lines(program));original=dict(lines)
    if len(original)!=len(lines) or not set([1000,*_DATA_LINES]) <= original.keys():
        return program,[]
    text={n:re.sub(r'\s+','',_line_text(b,kw.TOKEN)).upper() for n,b in lines}
    if text.get(1000)!=_REQUIRED_START:
        return program,[]
    # Refuse any alternate RESTORE or jump into this exact DATA span.
    for n,t in text.items():
        for entry in re.findall(r'\bRESTORE(\d+)',t):
            if 1010<=int(entry)<=1040 and (n!=1000 or entry!='1010'):
                return program,[]
        for target in re.findall(r'\bGO(?:TO|SUB)(\d+)',t):
            if 1010<=int(target)<=1040:
                return program,[]
    changes={};occurrences=0;fields_seen=0
    for line in _DATA_LINES:
        body=original[line]
        if not body.startswith(bytes((_DATA,))) or not body.endswith(b'\r'):
            return program,[]
        contents=body[1:-1]
        fields=_split_fields(contents)
        if len(fields)!=8:
            return program,[]
        transformed=[]
        for field in fields:
            cell=field.strip()
            if cell.lower()==b'a':
                occurrences+=1
                transformed.append(source.hide_numbers(b'0',fp))
            elif re.fullmatch(rb'(\d+)\x0e.{5}',cell,re.S):
                transformed.append(field)
            else:
                return program,[]
        fields_seen+=len(fields)
        changes[line]=bytes((_DATA,))+b','.join(transformed)+b'\r'
    if occurrences!=4 or fields_seen!=32:
        return program,[]
    return tap.join_lines([(n,changes.get(n,b)) for n,b in lines]),[{ 
        'initializer_line':1000,'restore':_START,'data_lines':list(_DATA_LINES),
        'read_count':32,'replaced_variable':'a','literal_value':0,
        'replaced_fields':4,
    }]
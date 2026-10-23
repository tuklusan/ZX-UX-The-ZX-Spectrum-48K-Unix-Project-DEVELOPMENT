"""Lower a bounded numeric DATA/READ grid with variable-valued DATA fields.

Only a plain RESTORE/DIM, two literal nested FOR loops, one READ, and
nexting both loops are supported.  Replacing the reads with ordinary LET
assignments preserves when DATA expressions are evaluated (on each call),
whereas embedding their values as compile-time constants would not.

The original program is untouched. This pass deliberately rejects other
flows, multiple reads, and any branch into the translated region.
"""
from __future__ import annotations
import re
from constant_data import _separate
from udg_bounds import _line_text


def _num_bytes(value, source, fp):
    return source.hide_numbers(str(value).encode('ascii'), fp)


def _number_field(b):
    b = b.strip()
    # Hidden Sinclair 5-byte number tail; do not guess alternate formats.
    m = re.fullmatch(rb'(0)\x0e\x00\x00\x00\x00\x00', b)
    return 0 if m else None


def _plain_var(field):
    f = field.strip()
    if len(f) == 1 and 65 <= f[0] <= 90 or len(f) == 1 and 97 <= f[0] <= 122:
        return f.lower().decode('ascii')
    return None


def _data_fields(body, data_token):
    pos = body.find(bytes((data_token,)))
    if pos < 0 or pos != 0 or body.count(bytes((data_token,))) != 1:
        return None
    tail = body[pos + 1:]
    if not tail.endswith(b'\r'):
        return None
    return _separate(tail[:-1])


def adapt_numeric_data_grid(program, kw, fp, source, tap):
    rows = list(tap.split_lines(program))
    decoded = [(n, _line_text(body, kw.TOKEN)) for n,body in rows]
    by_number = dict(rows)
    by_text = dict(decoded)
    numbers = [n for n,_ in rows]
    changes = {}
    proofs = []
    # Anchor on a RESTORE/DIM declaration, then validate the entire shape.
    for i in range(len(rows) - 10):
        head, stmt = decoded[i]
        h = re.fullmatch(r'\s*RESTORE\s*:\s*DIM\s+([a-z])\((\d+),(\d+)\)\s*', stmt, re.I)
        if not h:
            continue
        var, max_rows, width = h[1].lower(), int(h[2]), int(h[3])
        if not (1 <= max_rows <= 39 and 1 <= width <= 8):
            continue
        # Require the exact original loop pattern and consecutive source rows.
        loop_nums = numbers[i+1:i+6]
        loop_text = [by_text[n] for n in loop_nums]
        f1 = re.fullmatch(r'\s*FOR\s+([a-z])\s*=\s*1\s*TO\s*'+str(max_rows)+r'\s*',loop_text[0],re.I)
        f2 = re.fullmatch(r'\s*FOR\s+([a-z])\s*=\s*1\s*TO\s*'+str(width)+r'\s*',loop_text[1],re.I)
        if not f1 or not f2 or f1[1].lower() == f2[1].lower():
            continue
        rowvar, colvar=f1[1].lower(),f2[1].lower()
        if not re.fullmatch(r'\s*READ\s+'+var+r'\('+rowvar+r','+colvar+r'\)\s*',loop_text[2],re.I):
            continue
        if not re.fullmatch(r'\s*NEXT\s+'+colvar+r'\s*',loop_text[3],re.I):
            continue
        if not re.fullmatch(r'\s*NEXT\s+'+rowvar+r'\s*',loop_text[4],re.I):
            continue
        # All numeric DATA immediately follows the NEXT and precedes the
        # next array DIM; subsequent READs need an explicit RESTORE there.
        datarows=[]
        j=i+6
        while j<len(rows) and rows[j][1][:1] == bytes((kw.CODE_FOR['DATA'],)):
            datarows.append(rows[j]);j+=1
        if not datarows or j+3>=len(rows):
            continue
        next_number, next_text = decoded[j]
        first_data_later = decoded[j+3][0]
        if not re.fullmatch(r'\s*DIM\s+[a-z]\$\(\d+,\d+\)\s*',next_text,re.I):
            continue
        if not re.fullmatch(r'\s*FOR\s+[a-z]\s*=\s*1\s*TO\s*\d+\s*',decoded[j+1][1],re.I):
            continue
        if not re.fullmatch(r'\s*READ\s+[a-z]\$\([a-z]\)\s*',decoded[j+2][1],re.I):
            continue
        if rows[j+3][1][:1] != bytes((kw.CODE_FOR['DATA'],)):
            continue
        fields=[]
        for _,body in datarows:
            split=_data_fields(body,kw.CODE_FOR['DATA'])
            if split is None:
                fields=[];break
            fields.extend(split)
        if len(fields)!=max_rows*width:
            continue
        elements=[]
        usedvars=set()
        for field in fields:
            value=_number_field(field)
            if value==0:
                elements.append(None)
                continue
            name=_plain_var(field)
            if name is None or name in (var,rowvar,colvar):
                elements=[];break
            usedvars.add(name)
            elements.append(name)
        if len(elements)!=len(fields) or not usedvars:
            continue
        # The scalar sources are set before this routine is reached and
        # remain unchanged while this straight-line initialization executes.
        # No entry point into the replaced loop/data region is supported.
        start,end=loop_nums[0],datarows[-1][0]
        if end>=next_number or start+max_rows-1>=loop_nums[-1]:
            continue
        targets=re.findall(r'\b(?:GO\s*TO|GO\s*SUB|RESTORE)\s+(\d+)',
                           '\n'.join(t for _,t in decoded),re.I)
        if any(start<=int(t)<=end for t in targets):
            continue
        if any(n in by_number and n not in loop_nums for n in range(start,start+max_rows)):
            continue
        # Each row uses its own BASIC line, and only nonzero dynamic values
        # need assignments: DIM has already reset every numeric cell to 0.
        for row_index in range(max_rows):
            statements=[]
            for col_index in range(width):
                source_name=elements[row_index*width+col_index]
                if source_name is None:
                    continue
                statement=bytes((kw.CODE_FOR['LET'],))+var.encode('ascii')+b'(' \
                    + _num_bytes(row_index+1,source,fp)+b',' \
                    + _num_bytes(col_index+1,source,fp)+b')='+source_name.encode('ascii')
                statements.append(statement)
            changes[start+row_index]=(b':'.join(statements) if statements else bytes((kw.CODE_FOR['REM'],)))+b'\r'
        # Preserve the observable terminal FOR variables after both NEXTs.
        last_loop = loop_nums[-1]
        changes[last_loop]=(
            bytes((kw.CODE_FOR['LET'],))+rowvar.encode()+b'='+_num_bytes(max_rows+1,source,fp)
            +b':'+bytes((kw.CODE_FOR['LET'],))+colvar.encode()+b'='+_num_bytes(width+1,source,fp)+b'\r')
        for dnum,_ in datarows:
            changes[dnum]=bytes((kw.CODE_FOR['REM'],))+b'\r'
        # The next string READ must start at its own DATA, not at the now
        # empty numeric DATA (which could otherwise be skipped incorrectly).
        n,body=rows[j+1]
        changes[n]=bytes((kw.CODE_FOR['RESTORE'],))+_num_bytes(first_data_later,source,fp)+b':'+body[:-1]+b'\r'
        for n in loop_nums:
            if n not in changes:
                changes[n]=bytes((kw.CODE_FOR['REM'],))+b'\r'
        proofs.append({'array':var,'rows':max_rows,'columns':width,'fields':len(elements),
                       'scalar_inputs':sorted(usedvars),'last_line':last_loop,
                       'data_lines':[a for a,_ in datarows]})
        break
    if not changes:
        return program, []
    reserved={n for n,_ in rows}
    # Insert missing numbered lines, never replacing any non-template line.
    for n in changes:
        if n in reserved and n not in {a for a,_ in rows[i+1:i+6]} and n not in {a for a,_ in datarows} and n != rows[j+1][0]:
            raise AssertionError('numeric DATA rewrite crossed an existing BASIC line')
    output=dict(rows)
    output.update(changes)
    return tap.join_lines(sorted(output.items())),proofs
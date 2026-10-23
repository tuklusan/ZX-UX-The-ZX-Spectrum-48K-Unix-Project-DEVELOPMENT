"""Prove and specialize bounded custom-glyph DATA loops.

A fixed RESTORE, fixed glyph range and immediate literal initialization
allow literal DATA entries to be evaluated without changing original files.
Dynamic DATA statements or ambiguous control flow are never rewritten.
"""
from __future__ import annotations
import re
from constant_data import DATA, VAR, _separate
from udg_bounds import _line_text

_PATTERN = re.compile(
    r'^\s*RESTORE\s+(\d+)\s*:\s*'
    r'LET\s+([a-z])\s*=\s*(\d+)\s*:\s*'
    r'LET\s+([a-z])\s*=\s*(\d+)\s*:\s*'
    r'FOR\s+([a-z])\s*=\s*USR\s*"([a-z])"\s*TO\s*'
    r'USR\s*"([a-z])"\s*\+\s*7\s*:\s*'
    r'READ\s+([a-z])\s*:\s*POKE\s+([a-z])\s*,\s*\9\s*:\s*NEXT\s+\6\s*$',
    re.I,
)
_RESTORE = re.compile(r'\bRESTORE\s+(\d+)\b', re.I)
_RESTORE_ANY = re.compile(r'\bRESTORE\b', re.I)
_JUMP = re.compile(r'\bGO\s*(?:TO|SUB)\s+(\d+)\b', re.I)


def specialize_glyph_data(program, kw, fp, source, tap):
    rows = list(tap.split_lines(program))
    decoded = [(num, _line_text(body, kw.TOKEN)) for num, body in rows]
    row_by_num = dict(rows)
    if len(row_by_num) != len(rows):
        return program, []
    changes = {}
    proof = []
    for init_line, init_text in decoded:
        match = _PATTERN.fullmatch(init_text)
        if match is None:
            continue
        target = int(match[1]); letter_a, value_a = match[2].lower(), match[3]
        letter_b, value_b = match[4].lower(), match[5]
        glyph_first, glyph_last = ord(match[7].lower()), ord(match[8].lower())
        if glyph_last < glyph_first or not (ord('a') <= glyph_first <= glyph_last <= ord('u')):
            continue
        if letter_a == letter_b or match[9].lower() in (letter_a, letter_b):
            continue
        if not (0 <= int(value_a) <= 255 and 0 <= int(value_b) <= 255):
            continue
        values = {letter_a: value_a, letter_b: value_b}
        needed = (glyph_last - glyph_first + 1) * 8
        # No alternate RESTORE into the selected DATA sequence, and no
        # computed RESTORE anywhere in the listing.
        if any(_RESTORE_ANY.search(t) and len(_RESTORE.findall(t)) != len(_RESTORE_ANY.findall(t))
               for _, t in decoded):
            continue
        if sum(target == int(m[1]) for _, t in decoded for m in _RESTORE.finditer(t)) != 1:
            continue
        fields_total = 0
        picked = []
        for line, body in rows:
            if line < target:
                continue
            if fields_total >= needed:
                break
            # Each data line must contain DATA, and no other executable
            # statements; a boundary is not a license to read past it.
            if not body.lstrip(b' ').startswith(bytes((DATA,))):
                break
            stop = body.find(b'\r')
            if stop < 0:
                break
            data_pos = body.find(bytes((DATA,)))
            items = _separate(body[data_pos+1:stop])
            fields_total += len(items)
            if fields_total > needed:
                break
            picked.append((line, body, items, stop))
        if fields_total != needed or not picked:
            continue
        first, last = picked[0][0], picked[-1][0]
        if any(first <= int(m[1]) <= last and n != init_line
               for n, t in decoded for m in _RESTORE.finditer(t)):
            continue
        if any(first <= int(m[1]) <= last
               for _, t in decoded for m in _JUMP.finditer(t)):
            continue
        replacements = {}
        found = set()
        for line, body, items, stop in picked:
            updated = []
            for item in items:
                part = item.strip()
                if VAR.fullmatch(part):
                    name = part.decode('ascii').lower()
                    if name not in values:
                        replacements = None
                        break
                    found.add(name)
                    updated.append(item[:len(item)-len(item.lstrip())] +
                                   source.hide_numbers(values[name].encode('ascii'), fp) +
                                   item[len(item.rstrip()):])
                else:
                    updated.append(item)
            if replacements is None:
                break
            replacements[line] = body[:body.find(bytes((DATA,)))+1] + b','.join(updated) + body[stop:]
        if replacements is None or not found:
            continue
        if any(line in changes for line in replacements):
            continue
        changes.update(replacements)
        proof.append({'restore_line': init_line, 'data_first': first,
                      'data_last': last, 'glyph_count': glyph_last-glyph_first+1,
                      'entries': needed, 'constants': dict(values)})
    if not changes:
        return program, []
    return tap.join_lines([(n, changes.get(n, body)) for n, body in rows]), proof
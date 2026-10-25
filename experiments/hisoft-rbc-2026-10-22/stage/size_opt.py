"""Sound, general-purpose HiSoft string-capacity fitting.

Only complete literal assignments to scalar strings can establish bounds.
Any unknown write or indexed string use disqualifies the variable. Original
BASIC tokens are never modified.
"""
import re


def _statements(body, rem):
    quoted = False
    chunk = bytearray()
    p = 0
    while p < len(body):
        c = body[p]
        if c == 14 and not quoted:
            if p + 6 > len(body):
                return
            chunk.extend(body[p:p + 6])
            p += 6
            continue
        if c == 34:
            quoted = not quoted
        elif not quoted and c == rem:
            break
        elif not quoted and c in (58, 13):
            if chunk:
                yield bytes(chunk)
            chunk.clear()
            p += 1
            continue
        chunk.append(c)
        p += 1
    if chunk and not quoted:
        yield bytes(chunk)


def prove_literal_string_bounds(program, keywords, split_lines):
    code = keywords.CODE_FOR
    if not all(c in code for c in ('LET', 'REM', 'DIM', 'READ', 'INPUT')):
        return [], []
    rows = list(split_lines(program))
    # LEN and OPEN each need an unused preceding BASIC line number.
    if not rows or rows[0][0] < 2:
        return [], []
    exact = re.compile(rb'^\s*' + bytes([code['LET']]) +
                       rb'\s*([A-Za-z])\$\s*=\s*"([^"\r]*)"\s*$', re.I)
    writes = {}
    unsafe = set()
    for _, body in rows:
        for stmt in _statements(body, code['REM']):
            match = exact.fullmatch(stmt)
            if match:
                name = match.group(1).decode('ascii').upper()
                writes.setdefault(name, []).append(len(match.group(2)))
            for m in re.finditer(bytes([code['LET']]) +
                                 rb'\s*([A-Za-z])\$\s*(?:\(|=)', stmt, re.I):
                name = m.group(1).decode('ascii').upper()
                if not match or name != match.group(1).decode('ascii').upper():
                    unsafe.add(name)
            for word in ('DIM', 'READ', 'INPUT'):
                if bytes([code[word]]) in stmt:
                    unsafe.update(x.decode('ascii').upper()
                                  for x in re.findall(rb'([A-Za-z])\$', stmt, re.I))
            unsafe.update(x.decode('ascii').upper()
                          for x in re.findall(rb'\b([A-Za-z])\$\s*\(', stmt, re.I))
    sizes = {name: max(1, max(values)) for name, values in writes.items()
             if name not in unsafe and max(values) < 255}
    if not sizes:
        return [], []
    proofs = [{'variable': name + '$', 'max_chars': sizes[name],
               'literal_assignments': len(writes[name]),
               'saved_bss_bytes': 255 - sizes[name]} for name in sorted(sizes)]
    return ['LEN ' + ', '.join(f'{name}$<={sizes[name]}' for name in sorted(sizes))], proofs

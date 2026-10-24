"""Block machine-code USR; permit only statically proved UDG POKE addresses."""
from __future__ import annotations

import re
from audit_policy import scrub_code, split_address
from poke_proof import _line_text


class UnsupportedUsr(ValueError):
    pass


def _chunks(body):
    quoted = False
    current = bytearray()
    pos = 0
    while pos < len(body):
        c = body[pos]
        if not quoted and c == 0x0e:
            if pos + 5 >= len(body):
                raise UnsupportedUsr('RBC E_USR_TOKEN: Invalid numeric marker')
            current.extend(body[pos:pos + 6])
            pos += 6
            continue
        if not quoted and c == 0xea:
            break
        if c == 34:
            quoted = not quoted
        if c == 58 and not quoted:
            yield bytes(current)
            current.clear()
        elif c != 13:
            current.append(c)
        pos += 1
    yield bytes(current)


def _usr_tokens(body):
    quoted = False
    pos = 0
    count = 0
    while pos < len(body):
        b = body[pos]
        if not quoted and b == 14:
            pos += 6
            continue
        if b == 34:
            quoted = not quoted
        elif b == 0xc0 and not quoted:
            count += 1
        pos += 1
    return count


def enforce_numeric_usr(lines, findings, poke_proofs=None, token_names=None):
    """Permit USR only when it yields an exactly proved relocatable UDG POKE."""
    del findings
    token_names = token_names or {}
    proofs = poke_proofs or []
    for line, body in lines:
        for chunk in _chunks(body):
            token_count = _usr_tokens(chunk)
            if not token_count:
                continue
            source = _line_text(chunk, token_names)
            mask = scrub_code(source)
            matches = list(re.finditer(r'\bUSR\b', mask, re.I))
            if len(matches) != token_count:
                raise UnsupportedUsr(f'RBC E_USR_TOKEN: Line {line}: USR token cannot be classified')
            poke = re.search(r'\bPOKE\b', mask, re.I)
            if poke:
                address = split_address(source[poke.end():])
                if sum(m.start() >= poke.end() and
                       m.start() < poke.end() + len(source[poke.end():].split(',', 1)[0])
                       for m in matches) != token_count:
                    raise UnsupportedUsr(f'RBC E_USR_TOKEN: Line {line}: USR outside POKE address')
                relevant = [p for p in proofs if p['line'] == line and p['expression'] == address]
                if any(p.get('addresses') and
                       all(a['space'] == 'process_udg' and 0 <= a['offset'] < 168
                           for a in p['addresses']) for p in relevant):
                    continue
            frm = re.search(r'\bFOR\s+([a-z])\s*=', mask, re.I)
            if frm and all(m.start() > frm.end() for m in matches):
                var = frm.group(1)
                if any(p.get('addresses') and
                       all(a['space'] == 'process_udg' and 0 <= a['offset'] < 168
                           for a in p['addresses']) and
                       re.search(r'\b' + re.escape(var) + r'\b', p['expression'], re.I)
                       for p in proofs):
                    continue
            raise UnsupportedUsr(f'RBC E_USR_TOKEN: Line {line}: USR requires a proved UDG POKE address')

"""Supply missing Sinclair BASIC keyword boundaries in archived text listings.

Spectrum token entry can put a keyword immediately after a variable name.
The optional spaces here affect only the compiler's copy of a listing.
"""
from __future__ import annotations

import re


def normalize_listing(body: str) -> str:
    out = []
    i = start = 0
    quoted = False
    rem = False
    while i < len(body):
        c = body[i]
        if c == '"' and not rem:
            quoted = not quoted
            out.append(c)
            i += 1
            continue
        if not quoted and not rem and body[i:i + 3].upper() == 'REM':
            previous = body[i - 1] if i else ':'
            following = body[i + 3] if i + 3 < len(body) else ':'
            if not previous.isalnum() and not following.isalnum():
                rem = True
        if not quoted and not rem:
            prior = ''.join(out[start:])
            if body.startswith('THEN', i) and re.search(r'\bIF\b', prior, re.I):
                out.append(' THEN ')
                i += 4
                continue
            if body.startswith('TO', i) and re.search(
                r'\bFOR\s+[A-Za-z]\s*=\s*[A-Za-z]$', prior, re.I
            ):
                out.append(' TO ')
                i += 2
                continue
            if c == ':':
                out.append(c)
                i += 1
                start = len(out)
                continue
        out.append(c)
        i += 1
    # The Spectrum's power/arrow glyph is code 94 in both text and tape.
    return ''.join(out).replace('\u2191', '^')

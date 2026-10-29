"""Narrow, source-locked upper bound for Exocet's repeated string concatenation.

The 48K ROM workspace is not process-owned below the ZX-UX kernel.  Never
extend a variable merely because it happens to be named S$: the complete
original numbered source and the arithmetic below must agree first.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ORIGINAL_SHA256 = '85af9782454aa018786dd9feeca03b5a10785ca1ff59d1f08beb2d2e74515e0a'


def bounded_growth(src: Path) -> list[dict]:
    original = src.read_bytes()
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA256:
        return []
    rows = {}
    for raw in original.decode('ascii').splitlines():
        match = re.fullmatch(r'\s*(\d+)\s+(.+)', raw)
        if match is None or int(match[1]) in rows:
            raise ValueError('long-string proof: invalid source listing')
        rows[int(match[1])] = match[2].strip()
    required = {
        1170: r'DIM G\$\(10,6\)',
        1240: r'FOR x=1 TO 100',
        1250: r'LET S\$=S\$\+G\$\(INT \(RND\*10\)\+1\)',
        1260: r'NEXT x',
        1270: r'LET sc=0: LET S\$=S\$\+Q\$',
    }
    if any(re.fullmatch(pattern, rows.get(num, ''), re.I) is None
           for num, pattern in required.items()):
        raise ValueError('long-string proof: source shape differs')
    start = re.fullmatch(r'LET Q\$="( *)": LET S\$=Q\$', rows.get(1235, ''), re.I)
    if start is None or len(start[1]) != 32:
        raise ValueError('long-string proof: initial text differs')
    # S$ = Q$ + 100 rows of exactly 6 characters + Q$.
    limit = 2 * len(start[1]) + 100 * 6
    assert limit == 664
    return [{'variable': 'S$', 'max_chars': limit,
             'bound_proof': 'original-exocet-bounded-concatenation',
             'literal_assignments': 0}]


def workspace_bytes(proofs: list[dict]) -> int:
    return 1024 if any(p.get('bound_proof') ==
        'original-exocet-bounded-concatenation' and
        p.get('variable') == 'S$' and p.get('max_chars') == 664
        for p in proofs) else 0

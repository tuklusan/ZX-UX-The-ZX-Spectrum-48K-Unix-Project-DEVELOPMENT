#!/usr/bin/env python3
"""Adapt literal Spectrum ROM scroll-counter resets in temporary BASIC code.

ZX-UX screen writes do not use the ROM's scroll prompt counter. Remove only
plain POKE 23692,255 statements, leaving every other memory operation for
strict checking. Source text and tape files are never modified.
"""
from __future__ import annotations

import re


def _visible(data: bytes) -> bytes:
    out = bytearray()
    quoted = False
    i = 0
    while i < len(data):
        c = data[i]
        if c == 34:
            quoted = not quoted
        if not quoted and c == 14 and i + 5 < len(data):
            i += 6
            continue
        out.append(c)
        i += 1
    return bytes(out)


def _segments(body: bytes, rem: int):
    parts = []
    start = 0
    i = 0
    quoted = False
    while i < len(body):
        c = body[i]
        if c == 34:
            quoted = not quoted
        elif not quoted and c == 14 and i + 5 < len(body):
            i += 6
            continue
        elif not quoted and c == rem:
            break
        elif not quoted and c == 58:
            parts.append(body[start:i])
            start = i + 1
        i += 1
    parts.append(body[start:])
    return parts


def adapt_scroll_counter(program: bytes, keywords):
    import tap

    poke = keywords.CODE_FOR['POKE']
    rem = keywords.CODE_FOR['REM']
    pattern = re.compile(rb'\s*' + bytes([poke]) + rb'\s*23692\s*,\s*255\s*')
    changed = []
    rows = []
    for number, body in tap.split_lines(program):
        if not body.endswith(b'\r'):
            raise ValueError(f'invalid BASIC line ending at {number}')
        parts = _segments(body[:-1], rem)
        kept = []
        replaced = 0
        for part in parts:
            if pattern.fullmatch(_visible(part)):
                replaced += 1
            else:
                kept.append(part)
        if replaced:
            changed.extend([number] * replaced)
            revised = b':'.join(kept)
            if not revised.strip():
                revised = bytes([rem])
            rows.append((number, revised + b'\r'))
        else:
            rows.append((number, body))
    return tap.join_lines(rows), changed
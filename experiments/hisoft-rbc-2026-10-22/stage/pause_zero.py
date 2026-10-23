"""Expand only plain leading PAUSE 0 into a keyboard polling BASIC loop.

The original tape and text files are untouched. The compiler's temporary
program gets a new numbered continuation line when a colon follows PAUSE 0.
This addresses the native wait behavior observed in the Galaxians trial;
actual gameplay must still be checked on ZX-UX after compilation.
"""
from __future__ import annotations


def rewrite_pause_zero(program: bytes, keywords, fp):
    """Return (new_program, changes); never rewrite a computed PAUSE value.

    Only a stand-alone PAUSE 0 at the start of a line can be rewritten safely.
    A trailing colon splits the remaining statements into a free line before
    the next existing one, keeping GO SUB return flow intact. If no such line
    number exists, the source stays unchanged and the change is not reported.
    """
    import tap
    import source

    rows = tap.split_lines(program)
    known = {n for n, _ in rows}
    pause = keywords.CODE_FOR['PAUSE']
    result = []
    changes = []
    for index, (number, body) in enumerate(rows):
        pos = 0
        while pos < len(body) and body[pos] == 32:
            pos += 1
        if pos >= len(body) or body[pos] != pause:
            result.append((number, body))
            continue
        pos += 1
        while pos < len(body) and body[pos] == 32:
            pos += 1
        if pos >= len(body) or body[pos] != 48:
            result.append((number, body))
            continue
        pos += 1
        # A Spectrum numeric literal also has a marker and five stored bytes.
        if pos < len(body) and body[pos] == 0x0e:
            if pos + 6 > len(body):
                result.append((number, body))
                continue
            pos += 6
        while pos < len(body) and body[pos] == 32:
            pos += 1
        if pos >= len(body) or body[pos] not in (13, 58):
            result.append((number, body))
            continue
        has_more = body[pos] == 58
        next_free = number + 1
        if has_more and (next_free > 9999 or next_free in known):
            result.append((number, body))
            continue
        if has_more:
            # The new line must fall before the next existing BASIC line.
            after = [n for n in known if n > number]
            if after and next_free >= min(after):
                result.append((number, body))
                continue
        rewritten = (source.hide_numbers(
            source.tokenize_line(f'IF INKEY$="" THEN GO TO {number}', keywords), fp)
            + b'\r')
        result.append((number, rewritten))
        if has_more:
            remainder = body[pos + 1:]
            if not remainder.endswith(b'\r'):
                raise ValueError(f'BASIC line {number} lacks terminator')
            result.append((next_free, remainder))
        changes.append((number, next_free if has_more else None))
    return tap.join_lines(sorted(result)), changes

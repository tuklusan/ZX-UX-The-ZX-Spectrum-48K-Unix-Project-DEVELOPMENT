"""Expand safe PAUSE 0 statements into immediate keyboard polling loops.

All changes affect only the compiler's in-memory program; the original
Sinclair BASIC tapes and listings remain byte-for-byte unchanged.
PAUSE 0 waits for a key. INKEY$ is checked on every loop iteration and
is never read from buffered terminal input.
"""
from __future__ import annotations


def _wait_at(body: bytes, pause: int, rem: int):
    """Locate a plain PAUSE 0 at the start of an unconditional statement.

    Return (prefix, suffix) without the surrounding colon separators.
    Prefix and suffix each include their own BASIC statements but no CR.
    A line-wide IF may guard later colon-separated statements, so skip it.
    """
    pos = 0
    statement = 0
    colon = -1
    quoted = False
    previous_if = False
    while pos < len(body):
        char = body[pos]
        if char == 34:
            quoted = not quoted
            pos += 1
            continue
        if not quoted and char == 0x0e and pos + 6 <= len(body):
            pos += 6
            continue
        if not quoted and char == rem:
            break
        if not quoted and char == 0xfa:
            previous_if = True
        if not quoted and char == 58:
            colon = pos
            statement = pos + 1
            pos += 1
            continue
        if not quoted and char == pause and not previous_if:
            if body[statement:pos].strip(b' ') != b'':
                pos += 1
                continue
            end = pos + 1
            while end < len(body) and body[end] == 32:
                end += 1
            if end >= len(body) or body[end] != 48:
                pos += 1
                continue
            end += 1
            if end < len(body) and body[end] == 0x0e:
                if end + 6 > len(body):
                    pos += 1
                    continue
                end += 6
            while end < len(body) and body[end] == 32:
                end += 1
            if end >= len(body) or body[end] not in (13, 58):
                pos += 1
                continue
            before = body[:colon] if colon >= 0 else b''
            after = body[end + 1:-1] if body[end] == 58 else b''
            return before, after
        pos += 1
    return None


def rewrite_pause_zero(program: bytes, keywords, fp):
    """Return (temporary_program, line_changes) for safe literal waits.

    A leading wait stays on its original line. An inline wait gets a fresh
    line after its prefix. A trailing statement gets another free line.
    All inserted numbers must fit before the next existing line; otherwise
    that wait is preserved without rewriting it. Repeated waits are handled.
    """
    import tap
    import source

    rows = tap.split_lines(program)
    pause = keywords.CODE_FOR['PAUSE']
    rem = keywords.CODE_FOR['REM']
    changes = []
    # Each pass expands at most one PAUSE per line. The new continuation
    # can itself start with PAUSE; keep processing until no change remains.
    for _ in range(10000):
        known = {n for n, _ in rows}
        next_rows = []
        changed = False
        for number, body in rows:
            found = _wait_at(body, pause, rem)
            if found is None:
                next_rows.append((number, body))
                continue
            prefix, suffix = found
            wait_number = number + bool(prefix)
            continuation = wait_number + 1 if suffix else None
            allocated = [n for n in (wait_number, continuation) if n != number and n is not None]
            following = [n for n in known if n > number]
            limit = min(following) if following else 10000
            if any(n > 9999 or n in known or n >= limit for n in allocated):
                next_rows.append((number, body))
                continue
            if prefix:
                next_rows.append((number, prefix + b'\r'))
            rewritten = source.hide_numbers(
                source.tokenize_line(
                    f'IF INKEY$="" THEN GO TO {wait_number}', keywords), fp)
            next_rows.append((wait_number, rewritten + b'\r'))
            if suffix:
                next_rows.append((continuation, suffix + b'\r'))
            changes.append((number, wait_number, continuation))
            changed = True
        rows = sorted(next_rows)
        if not changed:
            return tap.join_lines(rows), changes
    raise ValueError('too many PAUSE 0 expansions in BASIC program')

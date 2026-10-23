"""Resolve literal GO TO and GO SUB targets using Sinclair's next-line rule.

This transforms only the compiler's in-memory tokenized copy. The original
BASIC files and their tape bytes stay untouched. Expressions and calculated
line numbers are intentionally left for a later compiler implementation.
"""
from __future__ import annotations

from bisect import bisect_left


def resolve_missing_targets(program: bytes, keywords, fp):
    """Map absent literal targets to the smallest existing larger line number.

    A literal must contain digits, an optional hidden numeric value, and a
    statement delimiter. Strings, REM text and calculated targets are skipped.
    Returns (rewritten_program, changes), with each change (source, old, new).
    """
    import tap
    lines = tap.split_lines(program)
    numbers = sorted(n for n, _ in lines)
    direct = {keywords.CODE_FOR['GO TO'], keywords.CODE_FOR['GO SUB']}
    rem = keywords.CODE_FOR['REM']
    changed = []
    rewritten = []
    for line_number, body in lines:
        out = bytearray()
        i = 0
        quote = False
        while i < len(body):
            c = body[i]
            if c == 34:
                quote = not quote
                out.append(c)
                i += 1
                continue
            if not quote and c == rem:
                out.extend(body[i:])
                break
            if not quote and c == 0x0e and i + 6 <= len(body):
                out.extend(body[i:i + 6])
                i += 6
                continue
            if not quote and c in direct:
                out.append(c)
                i += 1
                spaces = i
                while i < len(body) and body[i] == 32:
                    i += 1
                begin = i
                while i < len(body) and 48 <= body[i] <= 57:
                    i += 1
                digits_end = i
                end = i
                if i + 6 <= len(body) and body[i] == 0x0e:
                    end = i + 6
                # Never alter expressions such as GO TO 100+X.
                if begin < digits_end and (end == len(body) or body[end] in (13, 58)):
                    target = int(body[begin:digits_end])
                    at = bisect_left(numbers, target)
                    if at < len(numbers) and numbers[at] != target:
                        replacement = numbers[at]
                        out.extend(body[spaces:begin])
                        import source
                        out.extend(source.hide_numbers(str(replacement).encode('ascii'), fp))
                        changed.append((line_number, target, replacement))
                        i = end
                        continue
                out.extend(body[spaces:end])
                i = end
                continue
            out.append(c)
            i += 1
        rewritten.append((line_number, bytes(out)))
    return tap.join_lines(rewritten), changed

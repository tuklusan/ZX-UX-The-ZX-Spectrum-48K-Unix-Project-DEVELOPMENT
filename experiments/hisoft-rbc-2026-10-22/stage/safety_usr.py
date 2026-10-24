"""Refuse executable Sinclair BASIC USR tokens before native compilation.

Every executable 0xC0 token is prohibited, including the graphics-character
form. Only the genuine token stream matters: letters in quoted messages and
REM data have no executable meaning. The VAL guard is a separate runtime gate.
"""
from __future__ import annotations


class UnsupportedUsr(ValueError):
    """An executable BASIC line contains the forbidden 0xC0 keyword token."""


def enforce_numeric_usr(lines, findings):
    """Legacy entry point: block ALL executable USR tokens, not just numeric.

    Each record is the original Sinclair line-body bytes. Numeric literals
    have a six-byte cache beginning at 0x0E, which must never be interpreted
    as source code. DATA may include expressions evaluated by READ; its USR
    tokens are forbidden too. No address-classification exemption applies.
    """
    del findings  # A separate human-readable memory report cannot override tokens.
    for line, body in lines:
        quoted = False
        pos = 0
        while pos < len(body):
            byte = body[pos]
            if byte == 0x0e and not quoted:
                if pos + 5 >= len(body):
                    raise UnsupportedUsr(
                        f'RBC E_USR_TOKEN: Line {line}: Truncated BASIC numeric marker.')
                pos += 6
                continue
            if byte == 0xea and not quoted:  # REM: everything else is comment data.
                break
            if byte == 0x22:
                quoted = not quoted
            elif byte == 0xc0 and not quoted:
                raise UnsupportedUsr(
                    f'RBC E_USR_TOKEN: Line {line}: USR token 0xC0 is unsupported.')
            pos += 1

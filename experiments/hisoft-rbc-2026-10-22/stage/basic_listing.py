"""Strict numbered ASCII 48K BASIC adapter using the verified BAS2TAP port.

Only upstream BAS2TAP emits Sinclair bytes. No pyhsb tokenizer or numerical
metadata writer is permitted on the external BASIC source path.
"""
from __future__ import annotations
import re
from bas2tap import BAS2TAPError, encode_program

UPSTREAM_REVISION = '0ddb25e4c38ce4ccb5a43e85fb57e683bd274f59'
LINE = re.compile(r'[ \t]*([0-9]+)(?:[ \t]+(.*))?')


def split_numbered_line(raw: str) -> tuple[int, str]:
    match = LINE.fullmatch(raw)
    if not match:
        raise ValueError('expected numbered ASCII Sinclair BASIC')
    n = int(match.group(1))
    if n > 9999:
        raise ValueError('BASIC line number outside 0..9999')
    return n, match.group(2) if match.group(2) is not None else ''


def encode_strict_listing(listing: str) -> bytes:
    """Do not re-tokenize, clean, rewrite, or insert Spectrum line text."""
    if not listing.isascii():
        raise ValueError('non-ASCII Sinclair BASIC is unsupported')
    lines = listing.split('\n')
    seen = -1
    count = 0
    for index, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        number, body = split_numbered_line(raw[:-1] if raw.endswith('\r') else raw)
        if number <= seen:
            raise ValueError(f'line {index}: duplicate or unordered BASIC line {number}')
        if not body.strip() and count == 0:
            raise ValueError(f'line {index}: empty first BASIC statement')
        seen = number
        count += 1
    if not count:
        raise ValueError('empty BASIC listing')
    try:
        return encode_program(listing, case_insensitive=False, syntax_check=False)
    except BAS2TAPError as exc:
        raise ValueError(str(exc)) from exc

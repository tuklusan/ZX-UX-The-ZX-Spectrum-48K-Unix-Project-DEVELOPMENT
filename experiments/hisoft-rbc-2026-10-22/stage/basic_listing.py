"""Strict numbered ASCII 48K BASIC adapter using the verified BAS2TAP port.

Only upstream BAS2TAP emits Sinclair bytes. No pyhsb tokenizer or numerical
metadata writer is permitted on the external BASIC source path.
"""
from __future__ import annotations
import re
from bas2tap import BAS2TAPError, _prepare_line, tokenize_line

UPSTREAM_REVISION = '0ddb25e4c38ce4ccb5a43e85fb57e683bd274f59'
LINE = re.compile(r'[ \t]*([0-9]+)(?:(?:[ \t]+(.*))|(:.*))?')


def split_numbered_line(raw: str) -> tuple[int, str]:
    match = LINE.fullmatch(raw)
    if not match:
        raise ValueError('expected numbered ASCII Sinclair BASIC')
    n = int(match.group(1))
    if n > 9999:
        raise ValueError('BASIC line number outside 0..9999')
    return n, next((part for part in match.groups()[1:] if part is not None), '')


def _active_code(body: str) -> str:
    """Mask strings, REM and DATA without changing source positions."""
    chars = list(body)
    quoted = data = False
    pos = 0
    while pos < len(body):
        c = body[pos]
        boundary = pos == 0 or not (body[pos - 1].isalnum() or body[pos - 1] == '$')
        if (not quoted and boundary and body[pos:pos+3].upper() == 'REM' and
                (pos + 3 == len(body) or not (body[pos + 3].isalnum() or body[pos + 3] == '$'))):
            chars[pos:] = ' ' * (len(body) - pos)
            break
        if (not quoted and boundary and body[pos:pos+4].upper() == 'DATA' and
                (pos + 4 == len(body) or not (body[pos + 4].isalnum() or body[pos + 4] == '$'))):
            data = True
        if c == '"':
            quoted = not quoted
        elif c == ':' and not quoted:
            data = False
        if quoted or data or c == '"':
            chars[pos] = ' '
        pos += 1
    return ''.join(chars)


def _require_original_keyword_boundaries(number: int, body: str) -> None:
    """Reject FOR 1TO10 rather than manufacture a missing word boundary."""
    active = _active_code(body)
    for match in re.finditer(r'\bFOR\s+[A-Za-z]\s*=', active, re.I):
        tail = active[match.end():].split(':', 1)[0]
        if re.search(r'(?<=\d)TO(?=\d)', tail, re.I):
            raise ValueError(f'Line {number}: missing whitespace before TO in FOR statement')


def _fix_bin_cache(data: bytes, number: int) -> bytes:
    """Keep BIN numeric metadata consistent with the visible binary digits."""
    out = bytearray(data)
    quoted = False
    p = 0
    while p < len(out):
        c = out[p]
        if c == 34:
            quoted = not quoted
        elif not quoted and c == 0xEA:  # REM: remaining bytes are inert
            break
        elif not quoted and c == 14:  # previous numeric metadata
            if p + 6 > len(out):
                raise ValueError(f'Line {number}: incomplete numeric cache')
            p += 6
            continue
        elif not quoted and c == 0xC4:  # executable BIN token
            start = p + 1
            end = start
            while end < len(out) and out[end] in (48, 49):
                end += 1
            if end != start and end + 6 <= len(out) and out[end] == 14:
                value = int(out[start:end].decode('ascii'), 2)
                if value > 65535:
                    raise ValueError(f'Line {number}: BIN number exceeds 65535')
                out[end + 1:end + 6] = bytes((0, 0, value & 255, value >> 8, 0))
                p = end + 6
                continue
        p += 1
    return bytes(out)


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
        try:
            number, body = split_numbered_line(raw[:-1] if raw.endswith('\r') else raw)
        except ValueError as exc:
            raise ValueError(f'ASCII line {index}: {exc}: {raw[:48]!r}') from exc
        if number <= seen:
            raise ValueError(f'line {index}: duplicate or unordered BASIC line {number}')
        _require_original_keyword_boundaries(number, body)
        if not body.strip() and count == 0:
            raise ValueError(f'line {index}: empty first BASIC statement')
        seen = number
        count += 1
    if not count:
        raise ValueError('empty BASIC listing')
    # Spectrum records may exceed the C converter input buffer after ASCII
    # control escapes.  The Python version can tokenize the entire source.
    # Use upstream's preparer and lexer for every numbered line, without
    # introducing an alternative tokenizer or changing Sinclair code bytes.
    output = bytearray()
    mode = {'value': -1}
    seen = -1
    for index, raw in enumerate(lines, 1):
        if index == len(lines) and not raw:
            continue
        if raw.endswith('\r'):
            raw = raw[:-1]
        try:
            row = _prepare_line(raw, index, first=(seen == -1))
            if row is None:
                continue
            n, body = row
            if n <= seen:
                raise BAS2TAPError(f'Line {n}: duplicate or unordered BASIC line')
            data = _fix_bin_cache(tokenize_line(body, line_number=n, _mode=mode), n)
            output.extend(n.to_bytes(2, 'big'))
            output.extend(len(data).to_bytes(2, 'little'))
            output.extend(data)
            if len(output) > 41500:
                raise BAS2TAPError(f'Line {n}: program exceeds original 41500-byte limit')
            seen = n
        except BAS2TAPError as exc:
            raise ValueError(str(exc)) from exc
    return bytes(output)
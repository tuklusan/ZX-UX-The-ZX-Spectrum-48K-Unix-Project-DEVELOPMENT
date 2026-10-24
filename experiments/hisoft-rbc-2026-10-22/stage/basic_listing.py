"""Strict, external numbered ASCII Sinclair BASIC reader.

The adapter does not infer missing spaces or repair keyword spelling. The
original 48K ROM independently validates the resulting real token bytes.
"""
import re


def split_numbered_line(raw):
    match = re.fullmatch(r'[ \t]*(\d+)(?:[ \t]+(.*))?', raw)
    if not match:
        raise ValueError('expected numbered ASCII Sinclair BASIC')
    number = int(match.group(1))
    if not 0 <= number <= 9999:
        raise ValueError('BASIC line number outside 0..9999')
    return number, match.group(2) if match.group(2) is not None else ' '


def tokenize_preserving_numeric_at(body, source, kw):
    """Let the original Sinclair keyword map tokenize; do not change text."""
    if not body.isascii():
        raise ValueError('non-ASCII input: cannot infer Sinclair byte values')
    return source.tokenize_line(body, kw)
"""Supply missing Sinclair BASIC keyword boundaries in archived text listings.

Spectrum token entry can put a keyword immediately after a variable name.
The optional spaces here affect only the compiler's copy of a listing.
"""
from __future__ import annotations

import re


def split_numbered_line(raw: str) -> tuple[int, str]:
    """Decode a numbered text line without discarding a blank BASIC statement.

    An empty program line is stored as a single space before carriage return
    in the original Sinclair tape; it must not be lost by stripping the text.
    """
    match = re.fullmatch(r'(\d+)(?:[ \t]+(.*))?', raw.strip())
    if not match:
        raise ValueError('invalid numbered BASIC line')
    number = int(match.group(1))
    if number > 9999:
        raise ValueError('BASIC line number out of range')
    return number, match.group(2) or ' '


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
            # The original token can touch the last operand of a FOR
            # expression, including a product rather than just one variable.
            if (body.startswith('TO', i) and i > 0 and
                    (body[i - 1].isalnum() or body[i - 1] == ')') and
                    (i + 2 == len(body) or not body[i + 2].isalpha()) and
                    re.search(r'\bFOR\s+[A-Za-z]\s*=\s*.+$', prior, re.I)):
                out.append(' TO ')
                i += 2
                continue
            # A substring bound can join TO to its first operand.
            if (body.startswith('TO', i) and i > 0 and
                    (body[i - 1].islower() or body[i - 1] == ')') and
                    (i + 2 == len(body) or not body[i + 2].isalpha()) and
                    re.search(r'\$\([^)]*$', prior)):
                out.append(' TO ')
                i += 2
                continue
            # A FOR loop's STEP token can also touch the limit variable.
            if (body.startswith('STEP', i) and i > 0 and
                    (body[i - 1].islower() or body[i - 1].isdigit() or body[i - 1] == ')') and
                    (i + 4 == len(body) or not body[i + 4].isalpha()) and
                    re.search(r'\bFOR\s+[A-Za-z]\s*=\s*.+$', prior, re.I)):
                out.append(' STEP ')
                i += 4
                continue
            # Spectrum AND/OR tokens may touch a string variable's $ even
            # in LET, or a numeric expression in IF, without spaces.
            # An ordinary alphabetic identifier (e.g. BAND) stays intact.
            for operator in ('AND', 'OR'):
                # Only the original FL OR FL2 and DP OR LEN positions.
                extra_or = (operator == 'OR' and re.search(r'\bIF\b', prior, re.I)
                    and ((re.search(r'\bFL$', prior, re.I) and
                          re.match(r'\s+FL2\b', body[i + 2:], re.I))
                         or (re.search(r'\bDP$', prior, re.I) and
                             re.match(r'\s+LEN\b', body[i + 2:], re.I))))
                if (body.startswith(operator, i) and i > 0 and
                        (i + len(operator) == len(body) or
                         not body[i + len(operator)].isalpha()) and
                        (body[i - 1] == '$' or extra_or or
                         (re.search(r'\bIF\b', prior, re.I) and
                          (body[i - 1].islower() or
                           body[i - 1] in ')0123456789' or
                           (body[i - 1].isupper() and
                            re.search(r'(?:<>|<=|>=|[=<>])\s*[A-Z]$', prior)))))):
                    out.append(' ' + operator + ' ')
                    i += len(operator)
                    break
            else:
                operator = None
            if operator is not None:
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

# Four original PAYPACKETS statements use AT as a numeric variable. The
# Spectrum tape stores A,T rather than its PRINT-position keyword byte.
# Apply this only to those exact shapes; PRINT AT remains a keyword.
_NUMERIC_AT_FORMS = (
    (re.compile(r'\s*LET\s+AT\s*=\s*0\s*', re.I), 1),
    (re.compile(r'\s*LET\s+A\$\s*=\s*STR\$\s*\(\s*AT\s*\)\s*:\s*GO\s+TO\s+580\s*', re.I), 1),
    (re.compile(r'\s*IF\s+XX\s*=\s*1\s*THEN\s+LET\s+AT\s*=\s*AT\s*\+\s*B\(J\)\*V\(J\)\s*:\s*GO\s+TO\s+580\s*', re.I), 2),
    (re.compile(r'\s*LET\s+AT\s*=\s*AT\s*\+\s*A\(J\)\*V\(J\)\s*', re.I), 2),
)


def tokenize_preserving_numeric_at(body, source, kw):
    """Keep an unambiguous archived numeric identifier out of keyword space."""
    normalized = normalize_listing(body)
    tokenized = source.tokenize_line(normalized, kw)
    for pattern, count in _NUMERIC_AT_FORMS:
        if pattern.fullmatch(normalized):
            keyword = bytes((kw.CODE_FOR['AT'],))
            if tokenized.count(keyword) != count:
                raise ValueError('numeric AT identifier does not match text tokens')
            return tokenized.replace(keyword, b'AT')
    return tokenized

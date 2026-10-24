"""Convert original tokenized 48K BASIC to strictly numbered ASCII.

No BASIC text is repaired, and this converter never reads the paired .bas.
The caller must tokenize the result through RBC and compare every original
program byte before attempting compilation.
"""


class LosslessConversionError(ValueError):
    pass


def to_ascii_listing(lines, token_names):
    """Render existing Sinclair tokens without guessing any keyword boundary.

    The {HH} representation is an explicit byte literal handled by the
    existing RBC input adapter. Actual token bytes determine word boundaries.
    Literal spaces are written as {20}; spaces around rendered keywords are
    syntax-only separators and are discarded by the original keyword encoder.
    Numeric caches are supplied afresh by the original ROM number encoder;
    callers must compare their exact bytes after round-trip tokenization.
    """
    if not token_names:
        raise LosslessConversionError('missing original Sinclair token table')
    result = []
    for number, body in lines:
        if not isinstance(number, int) or not 0 <= number <= 9999:
            raise LosslessConversionError(f'BASIC line number {number!r} outside 0..9999')
        if not body or body[-1] != 13:
            raise LosslessConversionError(f'Line {number}: missing end-of-line marker')
        quoted = False
        rem = False
        rendered = []
        index = 0
        body = body[:-1]
        while index < len(body):
            value = body[index]
            if value == 14 and not quoted and not rem:
                if index + 6 > len(body):
                    raise LosslessConversionError(f'Line {number}: incomplete Sinclair numeric cache')
                index += 6
                continue
            if value == 34 and not rem:
                quoted = not quoted
            if not quoted and not rem and value in token_names:
                word = token_names[value].strip()
                if not word:
                    raise LosslessConversionError(f'Line {number}: empty Sinclair token name {value:02X}')
                rendered.append(' ' + word + ' ')
                if value == 0xEA:  # REM: the rest of the line is literal text.
                    rem = True
            else:
                # Encode every ordinary byte as an explicit literal. Raw
                # variable names can spell keyword text (such as AT), and
                # the keyword encoder must not silently retokenize them.
                rendered.append('{' + format(value, '02X') + '}')
            index += 1
        if quoted:
            raise LosslessConversionError(f'Line {number}: unmatched quoted string')
        result.append(str(number) + ' ' + ''.join(rendered))
    if not result:
        raise LosslessConversionError('empty original BASIC program')
    return '\n'.join(result) + '\n'


def confirm_roundtrip(original, recreated, split_lines):
    """Demand an exact byte match including numeric caches and quoted bytes."""
    if original == recreated:
        return
    a, b = split_lines(original), split_lines(recreated)
    for position in range(max(len(a), len(b))):
        if position >= len(a) or position >= len(b):
            raise LosslessConversionError('BASIC line count changed during token round-trip')
        n, original_body = a[position]
        m, recreated_body = b[position]
        if n != m:
            raise LosslessConversionError(f'BASIC line order changed: original {n}, round-trip {m}')
        if original_body != recreated_body:
            offset = next((i for i in range(min(len(original_body), len(recreated_body)))
                           if original_body[i] != recreated_body[i]),
                          min(len(original_body), len(recreated_body)))
            raise LosslessConversionError(
                f'Line {n}: token round-trip differs at byte {offset}; '
                f'original {original_body[offset:offset+5].hex().upper()}, '
                f'converted {recreated_body[offset:offset+5].hex().upper()}')
    raise LosslessConversionError('BASIC bytes changed during token round-trip')

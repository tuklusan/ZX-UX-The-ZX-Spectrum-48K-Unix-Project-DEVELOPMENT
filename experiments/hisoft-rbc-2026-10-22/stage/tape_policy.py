"""Block Sinclair tape I/O in standalone RBC programs.

Only original keyword tokens count; bytes inside strings, DATA fields,
REM text and hidden Sinclair numeric encodings are not instructions.
"""


class UnsupportedTapeOperation(ValueError):
    """A program needs a tape device at runtime, which RBC does not provide."""


TAPE_COMMANDS = frozenset({'LOAD', 'SAVE', 'MERGE', 'VERIFY'})


def reject_tape_operations(lines, token_names):
    """Reject executable 48K tape commands before compiler transformations."""
    codes = {
        code: word.strip().upper()
        for code, word in token_names.items()
        if word.strip().upper() in TAPE_COMMANDS
    }
    if set(codes.values()) != TAPE_COMMANDS:
        raise UnsupportedTapeOperation('RBC E_TAPE_UNSUPPORTED: missing original 48K tape tokens')

    for number, body in lines:
        in_string = False
        in_data = False
        pos = 0
        while pos < len(body):
            code = body[pos]
            if code == 34:  # Quotes can also occur in DATA.
                in_string = not in_string
                pos += 1
                continue
            if in_string:
                pos += 1
                continue
            if code == 14:  # Hidden five-byte Sinclair floating-point value.
                if pos + 6 > len(body):
                    raise UnsupportedTapeOperation(
                        f'RBC E_TAPE_UNSUPPORTED: Line {number}: truncated numeric token')
                pos += 6
                continue
            if code == 0xEA and not in_data:  # REM: the rest of this BASIC line is inert.
                break
            if code == 58:  # Next statement after a DATA field.
                in_data = False
                pos += 1
                continue
            if code == 0xE4 and not in_data:  # DATA, until an unquoted colon.
                in_data = True
                pos += 1
                continue
            if not in_data and code in codes:
                operation = codes[code]
                raise UnsupportedTapeOperation(
                    f'RBC E_TAPE_UNSUPPORTED: Line {number}: {operation} requires '
                    'external tape I/O; RBC supports standalone BASIC programs only')
            pos += 1

"""Reject external Spectrum channel commands before native code generation."""
from __future__ import annotations

PRINTER = frozenset({'LPRINT', 'LLIST'})
INTERFACE = frozenset({'CAT', 'FORMAT', 'MOVE', 'ERASE', 'OPEN #', 'CLOSE #'})
UNSUPPORTED = PRINTER | INTERFACE


class UnsupportedExternalIO(ValueError):
    pass


def reject_external_commands(lines, token_names):
    """Examine genuine token bytes; quoted strings and REM/DATA stay inert."""
    commands = {code: word.strip().upper() for code, word in token_names.items()
                if word.strip().upper() in UNSUPPORTED}
    if not PRINTER.issubset(set(commands.values())):
        raise UnsupportedExternalIO('RBC E_EXTERNAL_IO: 48K printer tokens absent')
    for number, body in lines:
        quoted = data = False
        i = 0
        while i < len(body):
            byte = body[i]
            if byte == 34:
                quoted = not quoted
            elif not quoted and byte == 14:
                if i + 6 > len(body):
                    raise UnsupportedExternalIO(
                        f'RBC E_EXTERNAL_IO: Line {number}: incomplete numeric bytes')
                i += 6
                continue
            elif not quoted and byte == 0xea and not data:
                break
            elif not quoted and byte == 58:
                data = False
            elif not quoted and byte == 0xe4 and not data:
                data = True
            elif not quoted and not data and byte in commands:
                name = commands[byte]
                category = 'printer' if name in PRINTER else 'Interface 1 channel'
                raise UnsupportedExternalIO(
                    f'RBC E_EXTERNAL_IO: Line {number}: {name} requires '
                    f'{category} support unavailable in standalone RBC')
            i += 1

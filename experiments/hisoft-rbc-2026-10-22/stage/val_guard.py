"""Source-level numeric VAL safety before native compilation.

Never treat a quoted print message or REM as executable code.  Dynamic VAL
is supported by the compiler frontend; its runtime operand must be checked
by native_val_rt before the ROM's unrestricted evaluator is reached.

This static pass rejects definitely executable literal numeric USR.  It is
not a replacement for the runtime guard, especially for INPUT and string
concatenation.  VAL$ is still unavailable until its own native guard exists.
"""
from __future__ import annotations

import re
from audit_policy import scrub_code
from poke_proof import _line_text, _statements

VAL_WORD = re.compile(r'(?<![A-Za-z0-9_$])VAL(?![A-Za-z0-9_$])', re.I)
VAL_STRING = re.compile(r'(?<![A-Za-z0-9_$])VAL\$(?![A-Za-z0-9_$])', re.I)
EXEC_USR = re.compile(r'(?<![A-Za-z0-9_$])USR(?![A-Za-z0-9_$])', re.I)


class UnsafeVal(ValueError):
    """Unsafe executable literal was encountered before native compilation."""


def _literal(tail):
    """Return the immediate string literal when exactly identifiable."""
    match = re.match(r'^\s*(\()?\s*"([^"]*)"\s*(\))?', tail)
    if not match:
        return None
    if bool(match.group(1)) != bool(match.group(3)):
        return None
    return match.group(2)


def guard_val(lines, token_names):
    checks = []
    for line, body in lines:
        source = _line_text(body, token_names)
        for part in _statements(source):
            mask = scrub_code(part)
            if VAL_STRING.search(mask):
                raise UnsafeVal(f'RBC E_VAL_EXPR: Line {line}: VAL$ runtime expression evaluation lacks a protected native entry')
            for found in VAL_WORD.finditer(mask):
                literal = _literal(part[found.end():])
                if literal is not None and EXEC_USR.search(literal):
                    raise UnsafeVal(f'RBC E_VAL_EXPR: Line {line}: executable numeric USR inside literal VAL')
                checks.append({'line': line, 'literal': literal,
                               'runtime_guard_required': literal is None})
    return checks

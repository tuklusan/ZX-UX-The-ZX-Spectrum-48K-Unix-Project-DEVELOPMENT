"""Reject runtime-evaluated BASIC text that could invoke numeric USR.

A numeric VAL literal is safe. Any expression-valued or user-controlled VAL
operand remains unsupported until a restricted numeric-only runtime parser is
proved. Never feed untrusted text to the Spectrum ROM's full BASIC evaluator.
"""
from __future__ import annotations

import re
from audit_policy import scrub_code
from poke_proof import _line_text, _statements

VAL_WORD = re.compile(r'(?<![A-Za-z0-9_$])VAL(?![A-Za-z0-9_$])',re.I)
VAL_STRING = re.compile(r'(?<![A-Za-z0-9_$])VAL\$(?![A-Za-z0-9_$])',re.I)
NUMERIC = re.compile(r'\s*[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?\s*\Z')


class UnsafeVal(ValueError):
    """A VAL operand cannot be shown to evaluate numeric text only."""


def guard_val(lines, token_names):
    safe=[]
    for line,body in lines:
        source=_line_text(body, token_names)
        for part in _statements(source):
            mask=scrub_code(part)
            if VAL_STRING.search(mask):
                raise UnsafeVal(f'RBC E_VAL_EXPR: Line {line}: VAL$ evaluates BASIC expression text; unsupported.')
            for m in VAL_WORD.finditer(mask):
                # Match literal operand only, optionally in a single pair of
                # parentheses. Anything computed may construct machine code.
                tail=part[m.end():]
                literal=re.match(r'^\s*(\()?\s*"([^"]*)"\s*(\))?',tail)
                if not literal or not NUMERIC.fullmatch(literal.group(2)):
                    raise UnsafeVal(f'RBC E_VAL_EXPR: Line {line}: VAL requires a proved numeric literal; '
                                    'dynamic BASIC expression evaluation is unsupported.')
                if bool(literal.group(1))!=bool(literal.group(3)):
                    raise UnsafeVal(f'RBC E_VAL_EXPR: Line {line}: VAL operand grouping is ambiguous.')
                after=tail[literal.end():].lstrip()
                if after and (after[0] in '+-.' or after[0]=='$'):
                    raise UnsafeVal(f'RBC E_VAL_EXPR: Line {line}: VAL text may be concatenated.')
                safe.append({'line':line,'numeric_text':literal.group(2)})
    return safe

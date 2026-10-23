"""Reject every unproved or numeric Spectrum USR before native compilation.

The graphics-character form is distinct: it returns a UDG address without
executing machine code. Keep the existing process-memory review independent.
"""
from __future__ import annotations

from audit_policy import audit_lines


class UnsupportedUsr(ValueError):
    """A source line would run machine code or lacks a safe character proof."""


def enforce_numeric_usr(lines, findings):
    """Fail even if a caller selects the non-strict memory-review setting.

    The token listing and reviewed memory findings must match per BASIC line,
    in source order. Refuse a mismatch rather than borrow an approval for a
    different USR expression on the same line.
    """
    operations = audit_lines(lines, 'tape')
    by_line = {}
    for f in findings:
        if f.operation == 'USR':
            by_line.setdefault(f.line, []).append(f)
    seen = {}
    for op in operations:
        if op['operation'] != 'USR':
            continue
        line = op['line']
        offset = seen.get(line, 0)
        seen[line] = offset + 1
        reviewed = by_line.get(line, [])
        if offset >= len(reviewed):
            raise UnsupportedUsr(f'RBC E_USR_TYPE: Line {line}: USR review mismatch; unsafe to compile.')
        check = reviewed[offset]
        kind = op['status']
        if kind == 'numeric_usr':
            raise UnsupportedUsr(
                f'RBC E_MACHINE_CODE: Line {line}: Numeric USR is unsupported. '
                'Direct execution of machine code is prohibited.')
        if kind == 'literal_graphics_character':
            continue  # Original process-memory review still applies.
        if (kind in ('string_expression_requires_type_and_range_proof',
                     'string_variable_requires_length_proof') and
                check.severity == 'info' and
                check.classification == 'process_udg_pointer'):
            continue  # An exact, previously reviewed graphics use, not numeric USR.
        raise UnsupportedUsr(
            f'RBC E_USR_TYPE: Line {line}: Cannot prove USR uses a safe '
            f'graphics-character string (source class: {kind}).')
    for line, reviewed in by_line.items():
        if seen.get(line, 0) != len(reviewed):
            raise UnsupportedUsr(
                f'RBC E_USR_TYPE: Line {line}: Unmatched USR operation in memory review.')

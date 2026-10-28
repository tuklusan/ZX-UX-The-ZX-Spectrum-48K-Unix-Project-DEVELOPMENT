"""Keep Z80 RAM reads during a full-source optimizer pass.

The optimizer may remove reloads after stores. ROM routines and interrupts
may update the same RAM location; zero-byte labels preserve those reads.
"""
from __future__ import annotations

import re


class VolatileFenceError(ValueError):
    """Memory source cannot be fenced without stable typed labels."""


_LABEL = re.compile(r'^([a-z_][a-z_0-9]*):$', re.I)
_READ = re.compile(r'^\s*ld\s+[^,()]+,\s*\([^)]*\)\s*(?:;.*)?$', re.I)
_SECTION = re.compile(r'^\s*section\s+(\w+)\s*$', re.I)


def protect_volatile_reads(assembly: str) -> str:
    """Fence typed text reads against load-after-store removal; keep bytes."""
    if not isinstance(assembly, str) or not assembly:
        raise VolatileFenceError('typed whole assembly required')
    lines = assembly.splitlines(keepends=True)
    labels = set()
    for line in lines:
        match = _LABEL.fullmatch(line.strip())
        if match:
            if match.group(1).lower() in labels:
                raise VolatileFenceError('duplicate typed source label')
            labels.add(match.group(1).lower())
    section = 'text'
    output = []
    found = 0
    for line in lines:
        match = _SECTION.fullmatch(line.strip())
        if match:
            section = match.group(1).lower()
        if section == 'text' and _READ.fullmatch(line.rstrip('\r\n')):
            name = f'__rbc_volatile_read_{found:05d}'
            if name in labels:
                raise VolatileFenceError('source owns volatile fence label')
            output.append(name + ':\n')
            found += 1
        output.append(line)
    return ''.join(output)


def strip_volatile_fences(candidate: str, fenced: str) -> str:
    """Discard only zero-byte labels added for the optimizer input."""
    names = {line.strip() for line in fenced.splitlines()
             if line.strip().startswith('__rbc_volatile_read_')
             and line.strip().endswith(':')}
    return ''.join(line for line in candidate.splitlines(keepends=True)
                   if line.strip() not in names)

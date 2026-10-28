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
_RESERVED = '__rbc_volatile_read_'


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
            if match.group(1).lower().startswith(_RESERVED):
                raise VolatileFenceError('source owns volatile fence label')
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


def _anchors(source: str) -> tuple[tuple[str, str], ...]:
    """Witness every reserved label and its immediately following RAM read."""
    if not isinstance(source, str):
        raise VolatileFenceError('typed source with volatile fences required')
    lines = source.splitlines()
    anchors = []
    seen = set()
    for index, line in enumerate(lines):
        label = _LABEL.fullmatch(line.strip())
        if not label or not label.group(1).lower().startswith(_RESERVED):
            continue
        name = label.group(1).lower()
        if (name in seen or index + 1 >= len(lines) or
                not _READ.fullmatch(lines[index + 1])):
            raise VolatileFenceError('missing or displaced volatile fence')
        seen.add(name)
        # Whitespace and comments are irrelevant; register and memory address
        # are not. The optimizer may not change either behind this boundary.
        mnemonic = lines[index + 1].partition(';')[0]
        anchors.append((name, re.sub(r'\s+', '', mnemonic).lower()))
    return tuple(anchors)


def strip_volatile_fences(candidate: str, fenced: str) -> str:
    """Strip only exact, anchored synthetic labels; reject lost boundaries."""
    expected = _anchors(fenced)
    observed = _anchors(candidate)
    if observed != expected:
        raise VolatileFenceError('volatile fence changed during optimization')
    permitted = {label + ':' for label, _ in expected}
    return ''.join(line for line in candidate.splitlines(keepends=True)
                   if line.strip().lower() not in permitted)

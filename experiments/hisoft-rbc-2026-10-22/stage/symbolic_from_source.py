"""Translate completely typed HiSoft emission sources to relocatable Z80.

The input is a source-ownership map, never a decoded or patched executable.
Refuse any unresolved byte, entry, branch, operand, or section boundary.
Runtime emitters and direct stores need their own typed sources first.
"""
from __future__ import annotations

import re

from symbolic_source_boundaries import SourceBoundaryError, inspect_source_boundaries
from symbolic_z80 import SymbolicProgram


class UnresolvedSourceProgram(ValueError):
    """An original producer lacks sufficient type information for assembly."""


def from_source(events, image: bytes, base: int, text_end: int, bss: int,
                assembler, *, entry_offsets=(0,)) -> SymbolicProgram:
    """Construct an entire typed source image and explicit entry labels."""
    try:
        ownership = inspect_source_boundaries(events, image, base, text_end,
                                              bss, assembler)
    except SourceBoundaryError as exc:
        raise UnresolvedSourceProgram(str(exc)) from exc
    if not ownership.fully_typed:
        raise UnresolvedSourceProgram(
            f'unresolved source bytes={ownership.unresolved_bytes}, '
            f'gaps={len(ownership.gaps)}, overlaps={len(ownership.overlaps)}')
    spans = sorted(ownership.spans, key=lambda s: s.start)
    if not spans or spans[0].start != 0 or spans[-1].end != len(image):
        raise UnresolvedSourceProgram('source sections do not cover complete image')
    if any(a.end != b.start for a, b in zip(spans, spans[1:])):
        raise UnresolvedSourceProgram('source section boundaries are not contiguous')
    if not entry_offsets or entry_offsets[0] != 0 or len(set(entry_offsets)) != len(entry_offsets):
        raise UnresolvedSourceProgram('start and distinct source entries required')

    instructions = {s.start for s in spans if s.kind in ('instruction',
                                                        'instruction-relocated')}
    if any(entry not in instructions for entry in entry_offsets):
        raise UnresolvedSourceProgram('entry does not name a source instruction')
    targets = {s.target for s in spans if s.kind == 'instruction-relocated'}
    if None in targets:
        raise UnresolvedSourceProgram('relocation target is missing')
    if any(t < 0 or t >= len(image) + bss for t in targets):
        raise UnresolvedSourceProgram('relocation points outside program storage')
    for span in spans:
        if span.kind == 'data-source' and span.start < text_end:
            raise UnresolvedSourceProgram('source DATA crosses executable boundary')
        if span.kind == 'inline-data' and span.end > text_end:
            raise UnresolvedSourceProgram('inline literal crosses BASIC DATA boundary')
        if span.kind != 'instruction-relocated':
            continue
        op = span.source.split(None, 1)[0].lower()
        if op in ('jp', 'call') and span.target not in instructions:
            raise UnresolvedSourceProgram('branch target lacks a source instruction')
        if span.target < text_end and span.target not in instructions:
            raise UnresolvedSourceProgram('source relocation targets inline literal')
    marks = set(entry_offsets) | targets
    for t in marks:
        if t < text_end and t not in instructions:
            raise UnresolvedSourceProgram('text label falls inside source instruction')
    def name(at):
        return 'start' if at == 0 else f'source_{at:04x}'

    program = SymbolicProgram()
    current = 'text'
    offset = 0
    for span in spans:
        desired = 'text' if span.start < text_end else 'data'
        if desired != current:
            program.section(desired)
            current = desired
        if span.start != offset:
            raise UnresolvedSourceProgram('unowned image byte')
        if span.start in marks:
            program.label(name(span.start), entry=span.start in entry_offsets)
        if span.kind in ('instruction', 'instruction-relocated'):
            if span.kind == 'instruction-relocated':
                source = span.source.replace('nn', name(span.target))
                if source == span.source:
                    raise UnresolvedSourceProgram('source relocation placeholder missing')
            else:
                source = span.source
                op = source.split(None, 1)[0].lower()
                # Bare numeric branch/control targets are not relocatable sources.
                if op in ('jp', 'call', 'jr', 'djnz') and source.strip().lower() != 'jp (hl)':
                    raise UnresolvedSourceProgram('untyped numeric control transfer')
                # A 16-bit immediate can encode a hidden program address.
                if re.search(r'\bld\s+(?:bc|de|hl|sp)\s*,\s*[-+$0-9]', source,
                             re.IGNORECASE):
                    raise UnresolvedSourceProgram('untyped 16-bit operand')
            program.instruction(source)
        elif span.kind in ('inline-data', 'data-source'):
            # Split protected source data only where an explicit typed label lands.
            stops = sorted(t for t in marks if span.start < t < span.end)
            begin = span.start
            for end in (*stops, span.end):
                program.binary(image[begin:end])
                if end in marks:
                    program.label(name(end), entry=end in entry_offsets)
                begin = end
        else:
            raise UnresolvedSourceProgram('non-symbolic source producer')
        offset = span.end
    if offset != len(image):
        raise UnresolvedSourceProgram('assembled image length mismatch')
    if bss:
        program.section('bss')
        boundary = len(image)
        for at in sorted(t for t in marks if len(image) <= t < len(image) + bss):
            program.reserve(at - boundary)
            program.label(name(at))
            boundary = at
        program.reserve(len(image) + bss - boundary)
    elif any(t >= len(image) for t in marks):
        raise UnresolvedSourceProgram('BSS relocation without BSS')
    program.assembly()  # Require ordered sections, defined entries and symbols.
    return program

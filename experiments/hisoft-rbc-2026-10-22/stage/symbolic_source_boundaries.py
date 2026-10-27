"""Fail-closed instruction/data ownership map from original HiSoft emit calls.

Only a source mnemonic or a source opcode joined to its relocation operand
may own executable instructions. Numeric emitters, runtime code, and BASIC DATA
remain unoptimized until their exact source boundaries have been resolved.
Never disassemble emitted bytes to fill a gap in the source trace.
"""
from __future__ import annotations

from dataclasses import dataclass

from symbolic_fragments import FragmentBoundaryError, inspect_fragments


class SourceBoundaryError(ValueError):
    """An emission cannot be assigned an unambiguous source footprint."""


@dataclass(frozen=True)
class SourceBoundary:
    start: int
    end: int
    kind: str
    source: str
    target: int | None = None


@dataclass(frozen=True)
class BoundaryMap:
    spans: tuple[SourceBoundary, ...]
    gaps: tuple[int, ...]
    overlaps: tuple[int, ...]
    mismatches: tuple[int, ...]
    instruction_bytes: int
    unresolved_bytes: int
    executable_instruction_count: int
    fully_typed: bool


def _encoded(assembler, source: str) -> bytes:
    try:
        return bytes(assembler(source))
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        raise SourceBoundaryError('invalid source Z80 mnemonic') from exc


def inspect_source_boundaries(events, image: bytes, base: int, data_start: int,
                              bss: int, assembler) -> BoundaryMap:
    """Account for all image bytes with their live source producer.

    This is an ownership audit, not optimizer approval: even completely owned
    bytes still require CFG, entry, address, and runtime-emitter conversion.
    """
    if not isinstance(image, bytes) or not 0 <= data_start <= len(image):
        raise SourceBoundaryError('invalid compiled text/data extent')
    if not 0 <= base <= 65535 or not 0 <= bss <= 65535:
        raise SourceBoundaryError('invalid link base or BSS size')
    spans = []
    emitted = []
    consumed = set()
    i = 0
    while i < len(events):
        event = events[i]
        kind = event.kind
        pos = event.position
        payload = event.data
        target = None
        if not isinstance(pos, int) or not isinstance(payload, bytes):
            raise SourceBoundaryError('source emission has invalid position or payload')
        if kind == 'opcode':
            text = event.source.strip()
            if text.count('nn') == 1 and i + 1 < len(events):
                operand = events[i + 1]
                if (operand.kind == 'relocation' and
                        operand.position == pos + len(payload) and
                        len(operand.data) == 2 and
                        isinstance(operand.symbol_offset, int)):
                    target = operand.symbol_offset
                    if not 0 <= target < len(image) + bss:
                        raise SourceBoundaryError('source relocation target outside image and BSS')
                    expected_operand = ((base + target) & 65535).to_bytes(2, 'little')
                    if operand.data != expected_operand:
                        raise SourceBoundaryError('source operand differs from link base')
                    candidate = _encoded(assembler, text.replace('nn', str((base + target) & 65535)))
                    if candidate != payload + operand.data:
                        raise SourceBoundaryError('source opcode/operand encoding differs')
                    payload = candidate
                    consumed.add(i + 1)
                    kind = 'instruction-relocated'
            if kind == 'opcode':
                kind = 'unpaired-opcode'
        elif kind == 'instruction':
            if payload != _encoded(assembler, event.source.strip()):
                raise SourceBoundaryError('source mnemonic encoding differs')
            try:
                fragments = inspect_fragments([event], image, data_start, assembler)
            except FragmentBoundaryError as exc:
                raise SourceBoundaryError(str(exc)) from exc
            for fragment in fragments:
                spans.append(SourceBoundary(fragment.site, fragment.end,
                                            fragment.kind, fragment.source))
                emitted.append(fragment.encoded)
            i += 1
            continue
        elif kind == 'relocation':
            target = event.symbol_offset
            if not isinstance(target, int) or not 0 <= target < len(image) + bss:
                raise SourceBoundaryError('source relocation target outside image and BSS')
            if payload != ((base + target) & 65535).to_bytes(2, 'little'):
                raise SourceBoundaryError('unpaired relocation differs from link base')
            kind = 'unpaired-relocation'
        elif kind not in ('word', 'byte', 'binary', 'runtime-opaque',
                          'data-source', 'direct-write', 'inline-data'):
            raise SourceBoundaryError('unknown source producer: ' + str(kind))
        if kind == 'inline-data' and pos + len(payload) > data_start:
            raise SourceBoundaryError('source literal crosses BASIC DATA boundary')
        if kind in ('instruction', 'instruction-relocated') and pos + len(payload) > data_start:
            raise SourceBoundaryError('source instruction crosses into BASIC DATA')
        if not payload:
            raise SourceBoundaryError('zero-length source producer')
        if not 0 <= pos <= len(image) - len(payload):
            raise SourceBoundaryError('source emission outside final image')
        spans.append(SourceBoundary(pos, pos + len(payload), kind, event.source, target))
        emitted.append(payload)
        i += 1
        while i in consumed:
            i += 1
    owner = [[] for _ in image]
    mismatches = set()
    for number, (span, source_bytes) in enumerate(zip(spans, emitted)):
        for offset, value in enumerate(source_bytes):
            absolute = span.start + offset
            owner[absolute].append(number)
            if image[absolute] != value:
                mismatches.add(absolute)
    gaps = tuple(i for i, contributors in enumerate(owner) if not contributors)
    overlaps = tuple(i for i, contributors in enumerate(owner) if len(contributors) != 1)
    typed = {'instruction', 'instruction-relocated', 'inline-data', 'data-source'}
    unresolved = tuple(i for i, contributors in enumerate(owner)
                       if (len(contributors) != 1 or
                           spans[contributors[0]].kind not in typed or
                           i in mismatches))
    instructions = [s for s in spans if s.kind in ('instruction', 'instruction-relocated')]
    return BoundaryMap(tuple(spans), gaps, overlaps, tuple(sorted(mismatches)),
                       sum(s.end - s.start for s in instructions),
                       len(unresolved), len(instructions),
                       not gaps and not overlaps and not mismatches and not unresolved)


def verify_three_source_maps(groups, bases) -> dict:
    """Prove source-owned boundaries are stable at three native link bases."""
    if len(groups) != 3 or len(bases) != 3 or len(set(bases)) != 3:
        raise SourceBoundaryError('three distinct native bases required')
    first = groups[0]
    signature = lambda m: tuple((s.start, s.end, s.kind, s.source, s.target)
                                for s in m.spans)
    if any(signature(other) != signature(first) or
           other.gaps != first.gaps or other.overlaps != first.overlaps or
           other.mismatches != first.mismatches or
           other.fully_typed != first.fully_typed or
           other.instruction_bytes != first.instruction_bytes or
           other.unresolved_bytes != first.unresolved_bytes
           for other in groups[1:]):
        raise SourceBoundaryError('source ownership changed across native bases')
    kinds = {}
    for span in first.spans:
        kinds[span.kind] = kinds.get(span.kind, 0) + span.end - span.start
    return {'source_instruction_count': first.executable_instruction_count,
            'source_instruction_bytes': first.instruction_bytes,
            'source_unresolved_bytes': first.unresolved_bytes,
            'source_gap_bytes': len(first.gaps),
            'source_overlap_bytes': len(first.overlaps),
            'source_mismatch_bytes': len(first.mismatches),
            'source_byte_kinds': kinds,
            'typed_source_ownership': first.fully_typed,
            'complete_program_symbolic': False}

"""Join independently sourced runtime emitters to original HiSoft events.

The caller supplies typed runtime statements and actual Z80 writer-PC traces.
This bridge does not decode compiled bytes, infer statements from machine code,
or turn an untyped vendor routine into an approved optimization candidate.
Every original runtime-opaque event must have exactly one typed witness in
all three compile passes; other compiler source events retain exact ownership.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from runtime_typed_source import RuntimeSourceError, typed_runtime_events
from gate8_original_runtime_types import N_ROUTINES
from symbolic_emit_sites import inspect_emit_sites, verify_three_emit_sites


class RuntimeBridgeError(ValueError):
    """A runtime source witness does not match its original compiler span."""


@dataclass(frozen=True)
class RuntimeWitness:
    number: int
    start: int
    end: int
    writes: tuple
    statements: tuple


_RT = re.compile(r'RT([1-9][0-9]*)\Z')


def splice_three_runtime_sources(events, images, bases, witnesses, assembler):
    """Replace ALL runtime-opaque spans only after a three-base source proof.

    The verification deliberately operates before the existing whole-program
    pipeline: its independent source maps still reject any surviving unknown
    emitter, untraced patch, data boundary or unresolved control target.
    """
    if (any(len(group) != 3 for group in (events, images, witnesses)) or
            len(bases) != 3 or len(set(bases)) != 3 or
            any(type(base) is not int or not 0 <= base <= 0xffff
                for base in bases) or
            any(not isinstance(image, bytes) for image in images)):
        raise RuntimeBridgeError('three valid original source passes required')
    output = []
    signatures = []
    site_groups = []
    totals = []
    for group, image, base, witness_group in zip(events, images, bases, witnesses):
        original = tuple(group)
        spans = []
        occupied = set()
        for event in original:
            if event.kind != 'runtime-opaque':
                continue
            match = _RT.fullmatch(event.source)
            if (match is None or not 1 <= int(match.group(1)) <= N_ROUTINES or
                    type(event.position) is not int or
                    not isinstance(event.data, bytes) or not event.data or
                    not 0 <= event.position < event.position + len(event.data) <= len(image) or
                    image[event.position:event.position + len(event.data)] != event.data):
                raise RuntimeBridgeError('unverified original runtime source span')
            start, end = event.position, event.position + len(event.data)
            if occupied.intersection(range(start, end)):
                raise RuntimeBridgeError('overlapping original runtime spans')
            occupied.update(range(start, end))
            spans.append((int(match.group(1)), start, end))
        if not spans:
            raise RuntimeBridgeError('no original runtime source spans')
        if any(a[0] >= b[0] or a[2] != b[1]
               for a, b in zip(spans, spans[1:])):
            raise RuntimeBridgeError('original runtime ordering or adjacency differs')
        # Any unrelated event overlapping the runtime region is an unverified
        # rewrite, even when it happened to write the same final bytes.
        if any(event.kind != 'runtime-opaque' and
               any(position in occupied for position in
                   range(event.position, event.position + len(event.data)))
               for event in original):
            raise RuntimeBridgeError('original compiler rewrote runtime bytes')
        witness_group = tuple(witness_group)
        if (len(witness_group) != len(spans) or
                any(not isinstance(w, RuntimeWitness) or
                    (w.number, w.start, w.end) != expected
                    for w, expected in zip(witness_group, spans))):
            raise RuntimeBridgeError('missing or reordered original runtime witness')
        replacement = {}
        signature = []
        for w in witness_group:
            if not isinstance(w.writes, tuple) or not isinstance(w.statements, tuple):
                raise RuntimeBridgeError('runtime producer or source statements missing')
            try:
                converted = typed_runtime_events(
                    w.writes, w.statements, image[w.start:w.end],
                    w.start, w.end, base, assembler)
            except RuntimeSourceError as exc:
                raise RuntimeBridgeError(f'RT{w.number}: {exc}') from exc
            replacement[(w.number, w.start, w.end)] = converted
            # Writer PC, source opcode and typed relocation target are stable.
            # Relocated output bytes themselves depend on the compilation base.
            signature.append((w.number, w.start, w.end,
                              tuple((s.position, s.emitter_pc, s.kind, s.source,
                                     s.symbol_offset, s.write_pcs)
                                    for s in w.statements)))
        converted_events = []
        for event in original:
            if event.kind == 'runtime-opaque':
                key = (int(_RT.fullmatch(event.source).group(1)), event.position,
                       event.position + len(event.data))
                converted_events.extend(replacement[key])
            else:
                converted_events.append(event)
        output.append(tuple(converted_events))
        signatures.append(tuple(signature))
        site_groups.append(inspect_emit_sites(
            item for converted in replacement.values() for item in converted))
        totals.append(sum(w.end - w.start for w in witness_group))
    if signatures[1:] != signatures[:1] * 2 or len(set(totals)) != 1:
        raise RuntimeBridgeError('original runtime typed source varies by compiler base')
    try:
        site_report = verify_three_emit_sites(site_groups, bases)
    except ValueError as exc:
        raise RuntimeBridgeError('original runtime writer PCs vary by compiler base') from exc
    return tuple(output), {
        'runtime_source_passes': 3,
        'runtime_source_routines': len(signatures[0]),
        'runtime_source_bytes': totals[0],
        'runtime_source_sites': site_report,
        'typed_runtime_source_spliced': True,
        'whole_program_optimized': False,
        'native_behavior_verified': False,
    }

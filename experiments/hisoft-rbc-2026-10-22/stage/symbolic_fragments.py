"""Split live HiSoft inline assembly at its original source statements.

An inline defb/defw is protected source data, even when its bytes resemble
executable instructions. No decoded output or post-link pattern scan is used.
Only source instruction events are split; opaque runtime emitters remain opaque.
"""
from __future__ import annotations

from dataclasses import dataclass


class FragmentBoundaryError(ValueError):
    """A source instruction fragment cannot be identified without guessing."""


@dataclass(frozen=True)
class Fragment:
    site: int
    end: int
    kind: str
    source: str
    encoded: bytes


def inspect_fragments(events, image: bytes, text_end: int, assembler):
    """Verify each statement in a source `emit` against the original bytes."""
    if not isinstance(image, bytes) or not 0 <= text_end <= len(image):
        raise FragmentBoundaryError('invalid executable source extent')
    result = []
    for event in events:
        if event.kind != 'instruction':
            continue
        if (not isinstance(event.source, str) or
                not isinstance(event.position, int) or
                not isinstance(event.data, bytes)):
            raise FragmentBoundaryError('malformed source instruction')
        parts = event.source.split(';')
        if any(not part.strip() for part in parts):
            raise FragmentBoundaryError('empty inline assembly statement')
        offset = event.position
        assembled = bytearray()
        for part in parts:
            source = part.strip()
            op = source.split(None, 1)[0].lower()
            if op in ('defb', 'defw'):
                kind = 'inline-data'
            else:
                kind = 'instruction'
            try:
                encoded = bytes(assembler(source))
            except (ValueError, TypeError, KeyError, IndexError) as exc:
                raise FragmentBoundaryError('invalid source fragment assembly') from exc
            if not encoded:
                raise FragmentBoundaryError('empty source fragment encoding')
            end = offset + len(encoded)
            if not 0 <= offset < end <= text_end:
                raise FragmentBoundaryError('fragment outside executable extent')
            if image[offset:end] != encoded:
                raise FragmentBoundaryError('source fragment differs from final image')
            result.append(Fragment(offset, end, kind, source, encoded))
            assembled.extend(encoded)
            offset = end
        if (assembled != event.data or
                offset != event.position + len(event.data)):
            raise FragmentBoundaryError('fragment sequence differs from HiSoft emission')
    if not result:
        raise FragmentBoundaryError('no source instruction fragments')
    sites = set()
    for fragment in result:
        extent = set(range(fragment.site, fragment.end))
        if sites.intersection(extent):
            raise FragmentBoundaryError('overlapping source instruction fragments')
        sites.update(extent)
    return tuple(result)


def verify_three_fragment_passes(groups, bases):
    """Match source statement boundaries over three distinct load addresses."""
    if len(groups) != 3 or len(bases) != 3 or len(set(bases)) != 3:
        raise FragmentBoundaryError('three distinct compilation bases required')
    first = groups[0]
    footprint = lambda records: tuple((f.site, f.end, f.kind) for f in records)
    if any(footprint(group) != footprint(first) for group in groups[1:]):
        raise FragmentBoundaryError('source fragment boundaries changed across bases')
    if any(f.source != g.source or f.encoded != g.encoded
           for group in groups[1:] for f, g in zip(first, group)
           if f.kind == 'inline-data'):
        raise FragmentBoundaryError('protected inline bytes changed across bases')
    changed_code = sum(any(g[i].source != first[i].source or
                           g[i].encoded != first[i].encoded for g in groups[1:])
                       for i, f in enumerate(first) if f.kind == 'instruction')
    protected = tuple(f for f in first if f.kind == 'inline-data')
    code = tuple(f for f in first if f.kind == 'instruction')
    return {
        'source_statement_count': len(first),
        'instruction_statements': len(code),
        'inline_data_statements': len(protected),
        'instruction_bytes': sum(len(f.encoded) for f in code),
        'protected_inline_bytes': sum(len(f.encoded) for f in protected),
        'code_statements_varying_across_bases': changed_code,
        'complete_program_symbolic': False,
    }

"""Check stable HiSoft compiler call sites for the final emission pass.

Call-site identifiers help distinguish literal values from addresses during
future type checking. A site name alone never licenses a numeric relocation.
"""
from __future__ import annotations

from dataclasses import dataclass


class EmitSiteError(ValueError):
    """An emission is missing its original compiler call site."""


_SOURCE_KINDS = frozenset(('instruction', 'opcode', 'relocation',
                           'word', 'byte', 'binary'))


@dataclass(frozen=True)
class SourceSite:
    position: int
    size: int
    kind: str
    site: str


def inspect_emit_sites(events) -> tuple[SourceSite, ...]:
    """Retain source call sites; do not infer roles from generated opcodes."""
    result = []
    for event in events:
        if event.kind not in _SOURCE_KINDS:
            continue
        name = getattr(event, 'source_site', None)
        if not isinstance(name, str) or ':' not in name:
            raise EmitSiteError('source emission lacks compiler call site')
        method, line = name.rsplit(':', 1)
        if not method.isidentifier() or not line.isdecimal() or int(line) <= 0:
            raise EmitSiteError('invalid compiler call site')
        if not isinstance(event.position, int) or event.position < 0:
            raise EmitSiteError('negative source emission position')
        if not isinstance(event.data, bytes) or not event.data:
            raise EmitSiteError('source emission has no bytes')
        result.append(SourceSite(event.position, len(event.data), event.kind,
                                 name))
    return tuple(result)


def verify_three_emit_sites(groups, bases) -> dict:
    """Require identical source calls and output extents at three link bases."""
    if len(groups) != 3 or len(bases) != 3 or len(set(bases)) != 3:
        raise EmitSiteError('three distinct native bases required')
    first = groups[0]
    if any(group != first for group in groups[1:]):
        raise EmitSiteError('compiler source call sites changed across bases')
    return {'source_emissions': len(first),
            'source_call_sites': len({e.site for e in first}),
            'source_emitted_bytes': sum(e.size for e in first),
            'typed_absolute_operands': False}

"""Classify HiSoft's live two-byte direct writes before symbolic assembly.

A source emitter's method identifies a word-length field or control target.
No completed executable is disassembled or rewritten. Unrecognized writes
fail closed. Cross-pass target checks are required before relocation is trusted.
"""
from __future__ import annotations

from dataclasses import dataclass


class UnresolvedSourcePatch(ValueError):
    """A source write cannot be represented as an exact typed word."""


@dataclass(frozen=True)
class SourceWord:
    site: int
    source: str
    kind: str
    value: int
    target: int | None


_TYPES = {'emit_string_inline': 'literal-length',
          'st_next': 'control-target',
          'st_deffn': 'control-target',
          'end_of_line': 'control-target',
          'spectrum_for': 'control-target'}


def from_emissions(events, image: bytes, code_base: int,
                   text_end: int) -> tuple[SourceWord, ...]:
    """Return typed source writes, rejecting partial or non-code references."""
    observed = []
    for event in events:
        if event.kind != 'direct-write':
            continue
        if not 1 <= len(event.data) <= 2:
            raise UnresolvedSourcePatch('unexpected direct source store length')
        observed.extend((event.position + n, event.source, value)
                        for n, value in enumerate(event.data))
    groups = []
    i = 0
    while i < len(observed):
        first = observed[i]
        if i + 1 == len(observed):
            raise UnresolvedSourcePatch('unpaired direct source byte')
        second = observed[i + 1]
        if (first[1] not in _TYPES or second[1] != first[1] or
                second[0] != first[0] + 1):
            raise UnresolvedSourcePatch('direct source word boundaries unresolved')
        if not (0 <= first[0] < len(image) - 1):
            raise UnresolvedSourcePatch('direct source patch outside image')
        if first[0] + 1 >= text_end:
            raise UnresolvedSourcePatch('direct source patch outside executable text')
        value = first[2] | second[2] << 8
        if image[first[0]:first[0] + 2] != bytes((value & 255, value >> 8)):
            raise UnresolvedSourcePatch('source write changed after capture')
        kind = _TYPES[first[1]]
        target = None
        if kind == 'control-target':
            target = (value - code_base) & 65535
            if target >= text_end:
                raise UnresolvedSourcePatch('computed control target outside code')
        groups.append(SourceWord(first[0], first[1], kind, value, target))
        i += 2
    occupied = set()
    for group in groups:
        footprint = {group.site, group.site + 1}
        if occupied.intersection(footprint):
            raise UnresolvedSourcePatch('overlapping source patch bytes')
        occupied.update(footprint)
    return tuple(groups)


def verify_three_passes(words, builds) -> dict:
    """All source addresses must relocate; source byte lengths must not."""
    if len(words) != 3 or len(builds) != 3:
        raise UnresolvedSourcePatch('three native build passes required')
    if len({run.base for run in builds}) != 3:
        raise UnresolvedSourcePatch('native build bases must be distinct')
    base = builds[0].base
    first = words[0]
    for candidate, run in zip(words[1:], builds[1:]):
        if len(candidate) != len(first):
            raise UnresolvedSourcePatch('source word sites changed between passes')
        delta = run.base - base
        for old, new in zip(first, candidate):
            if (old.site, old.source, old.kind) != (new.site, new.source, new.kind):
                raise UnresolvedSourcePatch('source word identity changed')
            expected = ((old.value + delta) & 65535) if old.kind == 'control-target' else old.value
            if new.value != expected or (new.target != old.target):
                raise UnresolvedSourcePatch('source word relocation did not track compile base')
    types = {name: sum(w.kind == name for w in first)
             for name in ('literal-length', 'control-target')}
    return {'verified_source_words': len(first),
            'verified_patch_bytes': 2 * len(first),
            'word_kinds': types}

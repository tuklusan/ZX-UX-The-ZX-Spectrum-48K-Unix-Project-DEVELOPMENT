"""Audit instruction mnemonics at their source emission boundaries.

Explicit HiSoft Z80 mnemonics and opcode templates can be recognized before
assembly, with every encoded byte checked against the actual source emitter.
This does not decode machine code, infer data boundaries, or approve opaque
runtime byte generators for optimization.
"""
from __future__ import annotations

from dataclasses import dataclass


class UnresolvedInstruction(ValueError):
    """A source instruction is not faithfully described by its mnemonic."""


@dataclass(frozen=True)
class InstructionSource:
    site: int
    instruction: str
    data: bytes
    kind: str
    overwritten: bool


def inspect_sources(events, image: bytes, assembler):
    records = []
    for event in events:
        if event.kind not in ('instruction', 'opcode'):
            continue
        text = event.source.strip()
        if not text:
            raise UnresolvedInstruction('empty source opcode or instruction')
        if event.kind == 'opcode':
            if text.count('nn') != 1:
                raise UnresolvedInstruction('opcode is not a typed word template')
            try:
                full = assembler(text.replace('nn', '0'))
            except (TypeError, ValueError, KeyError) as exc:
                raise UnresolvedInstruction('invalid source opcode template') from exc
            if len(full) < 3:
                raise UnresolvedInstruction('source word opcode is too short')
            encoded = bytes(full[:-2])
        else:
            try:
                encoded = bytes(assembler(text))
            except (TypeError, ValueError, KeyError) as exc:
                raise UnresolvedInstruction('invalid emitted instruction') from exc
        if encoded != event.data:
            raise UnresolvedInstruction('source mnemonic differs from emitted Z80 bytes')
        if (not encoded or event.position < 0 or
                event.position + len(encoded) > len(image)):
            raise UnresolvedInstruction('emitted source location out of code image')
        records.append(InstructionSource(
            event.position, text, encoded, event.kind,
            image[event.position:event.position + len(encoded)] != encoded))
    if not records:
        raise UnresolvedInstruction('no source Z80 instructions were emitted')
    return tuple(records)


def verify_three_sources(groups, bases):
    """Check source instruction locations, not just final binary signatures."""
    if len(groups) != 3 or len(bases) != 3 or len(set(bases)) != 3:
        raise UnresolvedInstruction('three distinct native builds required')
    first = groups[0]
    if not first:
        raise UnresolvedInstruction('no instructions to verify')
    for current in groups[1:]:
        if len(current) != len(first):
            raise UnresolvedInstruction('instruction source count differs')
        for old, new in zip(first, current):
            if ((old.site, old.kind, len(old.data), old.overwritten) !=
                    (new.site, new.kind, len(new.data), new.overwritten)):
                raise UnresolvedInstruction('instruction source locations differ')
    counts = {'mnemonic': sum(r.kind == 'instruction' for r in first),
              'word_opcode': sum(r.kind == 'opcode' for r in first)}
    return {'typed_source_events': len(first),
            'typed_source_bytes': sum(len(r.data) for r in first),
            'kind_counts': counts,
            'changed_after_source_emit': sum(r.overwritten for r in first),
            'source_mnemonic_changes_across_bases': sum(
                any(group[i].instruction != first[i].instruction for group in groups[1:])
                for i in range(len(first))),
            'fully_symbolic': False}

"""Fail-closed conversion of explicitly typed HiSoft runtime-emitter sources.

Each statement must be supplied independently of the emitted bytes, including
its emitting Z80 PC. A runtime write trace can verify source ownership but
cannot infer an instruction, a symbol, or an opaque resource from output.
Unidentified producers and rewrites remain unresolved.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable


class RuntimeSourceError(ValueError):
    """The original runtime emitter has no fully verified typed source."""


@dataclass(frozen=True)
class RuntimeStatement:
    position: int
    emitter_pc: int
    kind: str                    # instruction, literal, or relocated
    source: str                  # original mnemonic or defb/defw statement
    symbol_offset: int | None = None


def typed_runtime_events(writes: Iterable, statements: Iterable[RuntimeStatement],
                         image: bytes, start: int, end: int, base: int,
                         assembler: Callable[[str], Iterable[int]]):
    """Verify source statements against every actual runtime staging write.

    Return regular HiSoft capture events for existing source-boundary audits.
    A relocated instruction must have one terminal 16-bit ``nn`` operand.
    No byte is promoted from the completed program or a decoded binary.
    """
    from symbolic_capture import Emission

    if (not isinstance(image, bytes) or not isinstance(start, int) or
            not isinstance(end, int) or not isinstance(base, int) or
            not 0 <= start <= end or len(image) != end - start or
            not 0 <= base <= 0xffff or base + end > 0x10000):
        raise RuntimeSourceError('invalid runtime output or link address')
    sources = tuple(statements)
    records = tuple(writes)
    if not sources or (end > start and not records):
        raise RuntimeSourceError('runtime producer source or write trace missing')
    seen = set()
    site_at = {}
    for write in records:
        position = getattr(write, 'position', None)
        pc = getattr(write, 'emitter_pc', None)
        value = getattr(write, 'value', None)
        if (not isinstance(position, int) or not start <= position < end or
                not isinstance(pc, int) or not 0 <= pc <= 0xffff or
                not isinstance(value, int) or not 0 <= value <= 255):
            raise RuntimeSourceError('invalid or out-of-range runtime write')
        if position in seen:
            raise RuntimeSourceError('runtime rewrite lacks typed patch source')
        if image[position - start] != value:
            raise RuntimeSourceError('runtime writer disagrees with output')
        seen.add(position)
        site_at[position] = pc
    if len(seen) != end - start:
        raise RuntimeSourceError('runtime source has unobserved bytes')

    result = []
    cursor = start
    for statement in sources:
        if not isinstance(statement, RuntimeStatement):
            raise RuntimeSourceError('invalid typed source statement')
        if statement.position != cursor:
            raise RuntimeSourceError('runtime source has gap, overlap or wrong order')
        if (not isinstance(statement.emitter_pc, int) or
                not 0 <= statement.emitter_pc <= 0xffff or
                not isinstance(statement.source, str) or
                not statement.source.strip() or ';' in statement.source or
                '\n' in statement.source):
            raise RuntimeSourceError('runtime source location or statement invalid')
        kind = statement.kind
        source = statement.source.strip()
        if kind not in ('instruction', 'literal', 'relocated'):
            raise RuntimeSourceError('runtime source kind not typed')
        if kind == 'literal':
            if source.split(None, 1)[0].lower() not in ('defb', 'defw'):
                raise RuntimeSourceError('runtime literal lacks source data directive')
        elif source.split(None, 1)[0].lower() in ('defb', 'defw'):
            raise RuntimeSourceError('runtime source data declared executable')
        if kind == 'relocated':
            offset = statement.symbol_offset
            if (not isinstance(offset, int) or not 0 <= offset or
                    source.count('nn') != 1):
                raise RuntimeSourceError('runtime relocated operand has no target')
            # The target may be in another emitter, BASIC DATA or the BSS.
            # Whole-program symbol resolution checks actual storage bounds.
            target = base + offset
            if target > 0xffff:
                raise RuntimeSourceError('runtime relocation outside address space')
            encoded_source = source.replace('nn', str(target))
        else:
            if statement.symbol_offset is not None:
                raise RuntimeSourceError('runtime address has no relocation type')
            encoded_source = source
        try:
            encoded = bytes(assembler(encoded_source))
        except (ValueError, KeyError, IndexError, TypeError, OverflowError) as exc:
            raise RuntimeSourceError('runtime source cannot be assembled') from exc
        if not encoded or cursor + len(encoded) > end:
            raise RuntimeSourceError('runtime source extends outside output')
        if encoded != image[cursor - start:cursor - start + len(encoded)]:
            raise RuntimeSourceError('runtime source encoding differs from bytes')
        if any(site_at[p] != statement.emitter_pc for p in range(cursor, cursor + len(encoded))):
            raise RuntimeSourceError('runtime write PC differs from typed producer')
        if kind == 'relocated':
            if (len(encoded) < 3 or
                    encoded[-2:] != target.to_bytes(2, 'little')):
                raise RuntimeSourceError('runtime operand is not terminal 16-bit address')
            split = len(encoded) - 2
            result.append(Emission(cursor, 'opcode', source, encoded[:split]))
            result.append(Emission(cursor + split, 'relocation', str(offset),
                                   encoded[split:], offset))
        else:
            result.append(Emission(cursor, 'instruction', source, encoded))
        cursor += len(encoded)
    if cursor != end:
        raise RuntimeSourceError('runtime source does not cover complete emitter')
    return tuple(result)

"""Conservative control edges and register liveness over typed whole Z80 source.

All input comes from compiler-owned assembly, including source data and runtime
labels. This analyzer does not decode finished machine code. Unresolved indirect
edges and unmodelled instructions remain explicit; no rewrite is admitted here.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

_REGS = frozenset(('a', 'b', 'c', 'd', 'e', 'h', 'l', 'f', 'sp', 'ix', 'iy',
                   'mem', 'i', 'r', 'alt'))
_BYTE_REGS = frozenset(('a', 'b', 'c', 'd', 'e', 'h', 'l'))
_NAME = re.compile(r'[a-z_][a-z_0-9]*\Z')
_IMM = re.compile(r'(?:\$[0-9a-f]+|0x[0-9a-f]+|[0-9]+)\Z')
_COND = frozenset(('nz', 'z', 'nc', 'c', 'p', 'm', 'pe', 'po'))


class TypedCFGError(ValueError):
    """Typed input has invalid source sections or duplicate symbol ownership."""


@dataclass(frozen=True)
class _Instruction:
    opcode: str
    operand: str
    owner: str
    next_line: bool


def _effects(opcode: str, operand: str):
    """Unmodelled operations read and write all tracked state, by design."""
    if opcode == 'nop':
        return frozenset(), frozenset(), True
    parts = [s.strip() for s in operand.split(',')]
    if opcode == 'ld' and len(parts) == 2 and parts[0] in _BYTE_REGS:
        dst, src = parts
        if src in _BYTE_REGS:
            return frozenset((src,)), frozenset((dst,)), True
        if _IMM.fullmatch(src):
            return frozenset(), frozenset((dst,)), True
    if opcode in ('inc', 'dec') and operand in _BYTE_REGS:
        return frozenset((operand,)), frozenset((operand, 'f')), True
    if opcode in ('jr', 'jp', 'djnz', 'ret', 'call', 'rst', 'reti', 'retn'):
        return _REGS, _REGS, False
    return _REGS, _REGS, False


def inspect_typed_cfg_liveness(assembly: str) -> dict:
    """Inspect direct source edges; never infer a target from binary bytes."""
    if not isinstance(assembly, str) or not assembly:
        raise TypedCFGError('complete typed assembly text required')
    section = 'text'
    pending = []
    symbols = {}
    instructions = []
    barrier = False
    for raw in assembly.splitlines():
        line = raw.partition(';')[0].strip().lower()
        if not line:
            continue
        if line.startswith('section '):
            section = line.split(None, 1)[1]
            if section not in ('text', 'data', 'bss'):
                raise TypedCFGError('unknown source section')
            pending.clear()
            barrier = True
            continue
        if line.startswith('global '):
            continue
        if line.endswith(':'):
            name = line[:-1]
            if not _NAME.fullmatch(name) or name in symbols or name in pending:
                raise TypedCFGError('duplicate or invalid typed source label')
            pending.append(name)
            continue
        words = line.split(None, 1)
        op = words[0]
        if op in ('db', 'dw', 'ds', 'defb', 'defw'):
            for label in pending:
                symbols[label] = None
            pending.clear()
            barrier = True
            continue
        if section != 'text':
            raise TypedCFGError('executable instruction outside text section')
        here = len(instructions)
        for label in pending:
            symbols[label] = here
        owner = pending[-1] if pending else ''
        pending.clear()
        instructions.append(_Instruction(op, words[1] if len(words) == 2 else '',
                                         owner, not barrier))
        barrier = False
    for label in pending:
        symbols[label] = None
    if symbols.get('start') is None or not instructions:
        raise TypedCFGError('typed source start does not name an instruction')
    edges = []
    unresolved = []
    rom_edges = 0
    calls = 0
    for site, ins in enumerate(instructions):
        terms = [part.strip() for part in ins.operand.split(',') if part.strip()]
        op = ins.opcode
        flow = True
        if op in ('jp', 'jr', 'djnz', 'call'):
            calls += op == 'call'
            target = terms[-1] if terms else ''
            conditional = (len(terms) == 2 and terms[0] in _COND)
            if op == 'djnz':
                conditional = True
            flow = conditional or op == 'call'
            if _NAME.fullmatch(target):
                destination = symbols.get(target)
                if destination is None:
                    unresolved.append((site, target))
                else:
                    edges.append((site, destination))
            elif _IMM.fullmatch(target) and op in ('jp', 'call'):
                value = int(target[1:], 16) if target.startswith('$') else int(target, 0)
                if value < 0x4000:
                    rom_edges += 1
                else:
                    unresolved.append((site, target))
            else:
                unresolved.append((site, target))
        elif op in ('ret', 'reti', 'retn'):
            flow = op == 'ret' and ins.operand in _COND
        elif op == 'rst':
            rom_edges += 1
        if flow and site + 1 < len(instructions) and instructions[site+1].next_line:
            edges.append((site, site+1))
        elif flow and site + 1 < len(instructions):
            unresolved.append((site, 'protected-data-fallthrough'))
    entries = {symbols['start']}
    # Source references can identify external routine callbacks; without an
    # independently verified entry manifest, label-only guesses are forbidden.
    successors = {i: set() for i in range(len(instructions))}
    for a, b in edges:
        successors[a].add(b)
    seen = set()
    todo = list(entries)
    while todo:
        at = todo.pop()
        if at in seen:
            continue
        seen.add(at)
        todo.extend(successors[at] - seen)
    uses = []
    defines = []
    modelled = 0
    for ins in instructions:
        read, write, known = _effects(ins.opcode, ins.operand)
        uses.append(read)
        defines.append(write)
        modelled += known
    live_in = [set() for _ in instructions]
    live_out = [set() for _ in instructions]
    # Every exit may expose all registers and process-visible storage.
    changed = True
    passes = 0
    while changed:
        passes += 1
        if passes > 3 * len(instructions) + 1:
            raise TypedCFGError('register liveness did not converge')
        changed = False
        for site in range(len(instructions) - 1, -1, -1):
            live_after = set().union(*(live_in[x] for x in successors[site])) if successors[site] else set(_REGS)
            live_before = set(uses[site]) | (live_after - set(defines[site]))
            if live_after != live_out[site] or live_before != live_in[site]:
                live_out[site], live_in[site] = live_after, live_before
                changed = True
    return {
        'instruction_count': len(instructions),
        'source_owned_labels': len(symbols),
        'direct_cfg_edges': len(edges),
        'reachable_instructions': len(seen),
        'unreached_instructions': len(instructions)-len(seen),
        'unresolved_control_edges': len(unresolved),
        'first_unresolved_edges': unresolved[:5],
        'direct_calls': calls,
        'rom_transfer_edges': rom_edges,
        'register_effects_modelled': modelled,
        'register_effects_unknown': len(instructions)-modelled,
        'source_liveness_converged': True,
        'rewrite_safe_to_admit': False,
        'native_behavior_verified': False,
    }

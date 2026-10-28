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
_SYMBOL = re.compile(r'(?<![a-z_0-9])([a-z_][a-z_0-9]*)(?![a-z_0-9])')


class TypedCFGError(ValueError):
    """Typed input has invalid source sections or duplicate symbol ownership."""


@dataclass(frozen=True)
class _Instruction:
    opcode: str
    operand: str
    owner: str
    next_line: bool


def _effects(opcode: str, operand: str):
    """Unmodelled effects are opaque; even NOP changes the Z80 R register.

    An instruction fetch updates R's low seven bits (M1 refresh cycle).
    LD A,R makes that state observable, so deleting a seemingly idle opcode
    cannot be justified by register liveness that ignores instruction fetches.
    This is only a dependency approximation, not a timing/semantics proof.
    """
    if opcode == 'nop':
        return frozenset(('r',)), frozenset(('r',)), True
    parts = [s.strip() for s in operand.split(',')]
    if opcode == 'ld' and len(parts) == 2 and parts[0] in _BYTE_REGS:
        dst, src = parts
        if src in _BYTE_REGS:
            return frozenset((src, 'r')), frozenset((dst, 'r')), True
        if _IMM.fullmatch(src):
            return frozenset(('r',)), frozenset((dst, 'r')), True
    if opcode in ('inc', 'dec') and operand in _BYTE_REGS:
        # Z80 INC/DEC preserve carry. With flags tracked as one coarse 'f'
        # register, these instructions READ the previous flags as well as
        # writing the changed bits. Without the read, backward liveness
        # incorrectly kills carry before a later conditional transfer.
        return frozenset((operand, 'f', 'r')), frozenset((operand, 'f', 'r')), True
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
    exported_symbols = set()
    instructions = []
    symbolic_table_targets = set()
    table_expressions = []
    barrier = False
    for raw in assembly.splitlines():
        line = raw.partition(';')[0].strip().lower()
        if not line:
            continue
        if line.startswith('section '):
            # A label immediately before a section switch still owns an
            # address. It is never an instruction entry, but it must remain
            # defined so duplicate labels and direct branches are caught.
            for label in pending:
                symbols[label] = None
            section = line.split(None, 1)[1]
            if section not in ('text', 'data', 'bss'):
                raise TypedCFGError('unknown source section')
            pending.clear()
            barrier = True
            continue
        if line.startswith('global '):
            declared = [name.strip() for name in line[7:].split(',')]
            if not declared or any(not _NAME.fullmatch(name) for name in declared):
                raise TypedCFGError('invalid exported Z80 source label')
            exported_symbols.update(declared)
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
            if op in ('dw', 'defw') and len(words) == 2:
                # A word table can pass an entry address to an indirect JP,
                # ROM callback, or runtime routine without a direct CFG edge.
                for part in words[1].split(','):
                    expression = part.strip()
                    if _NAME.fullmatch(expression):
                        symbolic_table_targets.add(expression)
                    else:
                        table_expressions.append(expression)
            if op in ('db', 'defb') and len(words) == 2:
                # Byte-built pointers (HIGH/LOW and masks) also escape the
                # direct CFG. Their target cannot be inferred as a word edge.
                table_expressions.extend(part.strip() for part in
                                         words[1].split(','))
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
    # A global text label is callable by a separately linked object, runtime
    # trampoline, or shell entry even if this assembly contains no local JP.
    for name in exported_symbols:
        if name not in symbols:
            raise TypedCFGError('exported Z80 label is not defined: ' + name)
    exported_entries = {symbols[name] for name in exported_symbols
                        if symbols[name] is not None}
    edges = []
    unresolved = []
    rom_edges = 0
    calls = 0
    conditional_exit_sites = set()
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
                # Z80 accepts leading-zero *decimal* operands; Python's
                # int(text, 0) rejects them as old-style octal. Keep
                # source language syntax, not host-language guessing.
                if target.startswith('$'):
                    value = int(target[1:], 16)
                elif target.startswith('0x'):
                    value = int(target, 16)
                else:
                    value = int(target, 10)
                if value < 0x4000:
                    rom_edges += 1
                    if op == 'jp' and conditional:
                        conditional_exit_sites.add(site)
                else:
                    unresolved.append((site, target))
            else:
                unresolved.append((site, target))
        elif op in ('ret', 'reti', 'retn'):
            flow = op == 'ret' and ins.operand in _COND
            if flow:
                # Taken conditional RET exits to an unknown caller. Its
                # state is observable even when fallthrough instructions
                # overwrite the same registers.
                conditional_exit_sites.add(site)
        elif op == 'rst':
            rom_edges += 1
        if flow and site + 1 < len(instructions) and instructions[site+1].next_line:
            edges.append((site, site+1))
        elif flow and site + 1 < len(instructions):
            unresolved.append((site, 'protected-data-fallthrough'))
        elif flow:
            # Missing terminal transfer may enter DATA, BSS or unmapped RAM.
            # Do not count it as a clean process exit.
            unresolved.append((site, 'protected-data-fallthrough' if barrier
                               else 'end-of-code-fallthrough'))
    # Code addresses can be taken without a DW table or a direct branch:
    # LD HL,handler; PUSH HL; RET transfers through the return stack.
    # Other registers can similarly carry callbacks into runtime routines.
    # Any instruction operand naming a code label is a possible entry.
    # Arithmetic on such a pointer may instead enter part-way through an
    # instruction, which cannot be bounded by this instruction-level CFG.
    address_taken = set()
    unknown_pointer_expressions = []
    for site, ins in enumerate(instructions):
        if ins.opcode in ('jp', 'jr', 'djnz', 'call'):
            continue  # Direct edges and opaque jump operands were audited.
        for term in _SYMBOL.findall(ins.operand):
            if symbols.get(term) is None:
                continue
            operands = tuple(part.strip() for part in ins.operand.split(','))
            if term in operands:
                address_taken.add(symbols[term])
            else:
                unknown_pointer_expressions.append((site, ins.operand))
    for expression in table_expressions:
        for term in _SYMBOL.findall(expression):
            if symbols.get(term) is not None:
                unknown_pointer_expressions.append((-1, expression))
    entries = {symbols['start']} | exported_entries
    # Source references can identify external routine callbacks; without an
    # independently verified entry manifest, label-only guesses are forbidden.
    successors = {i: set() for i in range(len(instructions))}
    for a, b in edges:
        successors[a].add(b)
    def reachable(seeds):
        seen = set()
        todo = list(seeds)
        while todo:
            at = todo.pop()
            if at in seen:
                continue
            seen.add(at)
            todo.extend(successors[at] - seen)
        return seen

    direct_reachable = reachable(entries)
    # Treat every symbol used as a code-pointer word as an entry, even when
    # no direct CALL or JP names it. If any target is unresolved, a computed
    # jump might land at any instruction or even in the middle of one; this
    # count is only a conservative upper bound, never an optimization permit.
    table_entries = {symbols[name] for name in symbolic_table_targets
                     if symbols.get(name) is not None}
    indirect_or_unknown = bool(unresolved or unknown_pointer_expressions)
    possible = (set(range(len(instructions))) if indirect_or_unknown else
                reachable(entries | table_entries | address_taken))
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
    unresolved_sites = {site for site, _target in unresolved}
    changed = True
    passes = 0
    while changed:
        passes += 1
        if passes > 3 * len(instructions) + 1:
            raise TypedCFGError('register liveness did not converge')
        changed = False
        for site in range(len(instructions) - 1, -1, -1):
            live_after = (set().union(*(live_in[x] for x in successors[site]))
                          if successors[site] else set(_REGS))
            if site in unresolved_sites or site in conditional_exit_sites:
                # Conditional returns and ROM jumps expose the taken path;
                # they must not inherit only the source fallthrough's liveness.
                live_after.update(_REGS)
            live_before = set(uses[site]) | (live_after - set(defines[site]))
            if live_after != live_out[site] or live_before != live_in[site]:
                live_out[site], live_in[site] = live_after, live_before
                changed = True
    return {
        'instruction_count': len(instructions),
        'source_owned_labels': len(symbols),
        'direct_cfg_edges': len(edges),
        'reachable_instructions': len(possible),
        'unreached_instructions': len(instructions)-len(possible),
        'direct_cfg_reachable_instructions': len(direct_reachable),
        'symbolic_table_entry_instructions': len(table_entries),
        'exported_entry_instructions': len(exported_entries),
        'symbolic_address_entry_instructions': len(address_taken),
        'unresolved_pointer_expressions': len(unknown_pointer_expressions),
        'unknown_entry_reachability': indirect_or_unknown,
        'unresolved_exit_sites': len(unresolved_sites),
        'conditional_external_exit_sites': len(conditional_exit_sites),
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

"""Prove source-only deletions occur exclusively in unreachable Z80 code.

This intentionally supports only closed, register-local programs. External
callbacks, indirect jumps, memory operands, stack mutation, and address-taken
labels cannot enter the proof. The linked native source still needs its normal
size, relocation, data, and runtime checks.
"""
from __future__ import annotations

from difflib import SequenceMatcher
import re


class UnreachableRewriteError(ValueError):
    """The source control graph does not justify a changed instruction."""


_LABEL = re.compile(r'[a-z_][a-z_0-9]*\Z')
_REG = '(?:a|b|c|d|e|h|l)'
_LD_REG = re.compile(r'ld\s+' + _REG + r'\s*,\s*' + _REG + r'\Z')
_NUMBER = re.compile(r'(?:0x[0-9a-f]+|\$[0-9a-f]+|[0-9]+)\Z')
_REG_UNARY = re.compile(r'(?:inc|dec|or|and|xor|cp|sub)\s+' + _REG + r'\Z')


def _parse(text: str):
    if not isinstance(text, str) or not text.strip():
        raise UnreachableRewriteError('typed full source required')
    section = ''
    code = []
    tags = []
    symbols = {}
    globals_ = []
    section_order = {'text': 0, 'data': 1, 'bss': 2}
    last_section = -1
    for raw in text.splitlines():
        line = raw.partition(';')[0].strip().lower()
        if not line:
            continue
        fields = line.split(None, 1)
        if fields[0] == 'section':
            if len(fields) != 2 or fields[1] not in ('text', 'data', 'bss'):
                raise UnreachableRewriteError('unknown section')
            section = fields[1]
            if section_order[section] <= last_section:
                raise UnreachableRewriteError('source section repeats or rewinds')
            last_section = section_order[section]
            tags.append(('section', section, None))
            continue
        if fields[0] == 'global':
            if len(fields) != 2 or fields[1] != 'start':
                raise UnreachableRewriteError('external entry can reach dead code')
            globals_.append('start')
            tags.append(('global', 'start', None))
            continue
        if line.endswith(':'):
            label = line[:-1]
            if not _LABEL.fullmatch(label) or label in symbols:
                raise UnreachableRewriteError('duplicate or invalid source label')
            symbols[label] = (section, len(code))
            tags.append(('label', label, None))
            continue
        if section == 'text':
            compact = re.sub(r'\s*,\s*', ',', line)
            compact = re.sub(r'\s+', ' ', compact)
            if not (compact == 'ret' or compact == 'nop' or
                    _LD_REG.fullmatch(compact) or _REG_UNARY.fullmatch(compact) or
                    re.fullmatch(r'(?:jp|jr) [a-z_][a-z_0-9]*', compact)):
                raise UnreachableRewriteError('unmodelled instruction or indirect entry')
            index = len(code)
            tags.append(('instruction', compact, index))
            code.append(compact)
        elif section in ('data', 'bss'):
            # Do not admit byte-built pointers or symbolic DATA entries.
            if (fields[0] not in ('db', 'dw', 'ds', 'defb', 'defw', 'defs') or
                    len(fields) != 2 or
                    any(not _NUMBER.fullmatch(item.strip())
                        for item in fields[1].split(','))):
                raise UnreachableRewriteError('unknown source data pointer')
            tags.append(('data', line, None))
        else:
            raise UnreachableRewriteError('source statement outside a section')
    if globals_ != ['start'] or symbols.get('start') is None:
        raise UnreachableRewriteError('closed program needs one start entry')
    if symbols['start'][0] != 'text' or not code:
        raise UnreachableRewriteError('start must be executable')
    for section_name, address in symbols.values():
        if section_name == 'text' and address >= len(code):
            raise UnreachableRewriteError('dangling text label')
    return tags, code, symbols


def check_unreachable_deletions(original: str, candidate: str) -> dict:
    """Return a closed-graph proof or reject all changed-code claims."""
    before, instructions, labels = _parse(original)
    after, _other, _new_labels = _parse(candidate)
    reachable = set()
    pending = [labels['start'][1]]
    while pending:
        i = pending.pop()
        if i in reachable:
            continue
        if i >= len(instructions):
            raise UnreachableRewriteError('reachable control falls outside text')
        reachable.add(i)
        op = instructions[i]
        if op == 'ret':
            continue
        if op.startswith(('jp ', 'jr ')):
            symbol = op.split()[1]
            target = labels.get(symbol)
            if target is None or target[0] != 'text':
                raise UnreachableRewriteError('unresolved direct control edge')
            pending.append(target[1])
        else:
            pending.append(i + 1)
    deleted = []
    for tag, low, high, new_low, new_high in SequenceMatcher(
            a=[(kind, statement) for kind, statement, _ in before],
            b=[(kind, statement) for kind, statement, _ in after],
            autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        if tag != 'delete' or new_low != new_high:
            raise UnreachableRewriteError('candidate is not source-only deletion')
        for kind, _statement, index in before[low:high]:
            if kind != 'instruction' or index in reachable:
                raise UnreachableRewriteError('deleted code can be an entry or resource')
            deleted.append(index)
    if not deleted:
        raise UnreachableRewriteError('no unreachable instructions deleted')
    return {'closed_control_graph': True,
            'deleted_unreachable_instructions': len(deleted),
            'reachable_source_instructions': len(reachable),
            'unreachable_source_instructions': len(instructions) - len(reachable)}

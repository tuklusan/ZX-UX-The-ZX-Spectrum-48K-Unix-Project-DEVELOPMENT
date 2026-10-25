"""Run upeepz80 on symbolic Z80 before HiSoft encodes instruction bytes.

Optimize only straight-line fragments without relocations, branches,
embedded data, or hardware interactions. The same transformation runs in
all compiler passes so generated offsets are consistent.
"""
from __future__ import annotations
from functools import lru_cache
import re

UPSTREAM_REVISION = 'a48d725704b132c3ff23ac77232a3a412b56b15f'
_BARRIERS = frozenset(('jr', 'djnz', 'jp', 'call', 'ret', 'reti', 'retn',
                      'rst', 'halt', 'defb', 'defw', 'db', 'dw', 'ds',
                      'org', 'di', 'ei', 'out', 'in', 'ex', 'exx'))

def _instructions(fragment):
    parts = [p.strip() for p in fragment.split(';') if p.strip()]
    if len(parts) < 2:
        return None
    for ins in parts:
        if re.match(r'^[a-z_][a-z_0-9]*:', ins, re.I):
            return None
        if ins.lower().split(' ', 1)[0] in _BARRIERS:
            return None
    return parts

def optimize_fragment(source, optimizer, asm):
    """Only shorter and assemblable unbranched Z80 may replace source."""
    parts = _instructions(source)
    if parts is None:
        return source, 0
    try:
        before = asm(source)
        optimized = optimizer.optimize(''.join('    ' + part + '\n' for part in parts))
        if not isinstance(optimized, str):
            raise ValueError('optimizer must return text')
        lines = [s.partition(';')[0].strip() for s in optimized.splitlines()
                 if s.partition(';')[0].strip()]
        transformed = '; '.join(lines)
        if _instructions(transformed) is None:
            return source, 0
        after = asm(transformed)
        if 0 < len(after) < len(before):
            return transformed, len(before) - len(after)
    except (ValueError, TypeError, IndexError, KeyError):
        pass
    return source, 0

def install(compiler):
    """Install on Compiler.emit() before its call to z80asm.asm()."""
    if getattr(compiler.Compiler, '_zxux_upeepz80_codegen', False):
        return
    from upeepz80 import PeepholeOptimizer
    from z80asm import asm
    original = compiler.Compiler.emit
    optimizer = PeepholeOptimizer()
    @lru_cache(maxsize=4096)
    def transform(rendered):
        return optimize_fragment(rendered, optimizer, asm)
    def emit(self, text, *vals):
        rendered = text.format(*vals) if vals else text
        replacement, saved = (rendered, 0) if self.probing else transform(rendered)
        if getattr(self, 'storing', False):
            stats = getattr(self, '_zxux_upeep_stats', None)
            if stats is None:
                stats = {'symbolic_fragments_seen': 0, 'shortened_fragments': 0,
                         'pre_assembly_bytes_saved': 0}
                self._zxux_upeep_stats = stats
            stats['symbolic_fragments_seen'] += 1
            if saved:
                stats['shortened_fragments'] += 1
                stats['pre_assembly_bytes_saved'] += saved
        return original(self, replacement)
    compiler.Compiler.emit = emit
    compiler.Compiler._zxux_upeepz80_codegen = True

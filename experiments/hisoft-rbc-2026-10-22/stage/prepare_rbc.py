#!/usr/bin/env python3
"""Apply the development extensions to the preserved RBC checkpoint."""
from pathlib import Path
import shutil
import sys


def prepare(checkpoint: Path, extensions: Path):
    # The checkout and the source tape collection remain untouched.
    compiler = checkpoint / 'rbc' / 'rbc.py'
    text = compiler.read_text()
    old = 'from memory_safety import MemoryBlocked, analyze_lines, enforce, summarize'
    new = 'from line_targets import resolve_missing_targets\n' + old
    if text.count(old) != 1 or text.count('program = source.tokenize_directives(program,kw)') != 1:
        raise ValueError('RBC checkpoint changed; extension location needs review')
    text = text.replace(old, new, 1)
    old = 'program = source.tokenize_directives(program,kw)'
    text = text.replace(old, old + '\n        program, next_lines = resolve_missing_targets(program, kw, initial.fp)', 1)
    text = text.replace("'memory_policy':memory_policy, 'memory_check':memory_report}",
                        "'memory_policy':memory_policy, 'memory_check':memory_report,\n"
                        "                        'next_line_targets':next_lines}", 1)
    memory = checkpoint / 'rbc' / 'memory_safety.py'
    memory_source = memory.read_text()
    old_target = 'target=_target(address)'
    if memory_source.count(old_target) != 1:
        raise ValueError('RBC memory guard changed; UDG fix needs review')
    memory_source = memory_source.replace(
        old_target, "target=_target(('USR ' if op=='USR' else '') + address)", 1)
    memory.write_text(memory_source)
    shutil.copyfile(extensions / 'line_targets.py', checkpoint / 'rbc' / 'line_targets.py')
    compiler.write_text(text)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: prepare_rbc.py CHECKPOINT_DIR EXTENSIONS_DIR')
    prepare(Path(sys.argv[1]), Path(sys.argv[2]))

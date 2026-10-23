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
    # The ROM recognizes an in-memory line zero. HiSoft needs OPEN before
    # the first source line even when the archive starts with line one.
    before = '            program = source.add_directives(program, directives, True, [], kw, initial.fp)'
    after = "            try:\n                program = source.add_directives(program, directives, True, [], kw, initial.fp)\n            except source.SourceError as exc:\n                if directives or 'no free line numbers' not in str(exc):\n                    raise\n                program = source.add_directives(program, [], False,\n                                                ['0 REM : OPEN #'], kw, initial.fp)"
    if text.count(before) != 1:
        raise ValueError('RBC OPEN directive placement changed')
    text = text.replace(before, after, 1)
    old_read = "src.read_text(encoding='latin-1').splitlines()"
    if text.count(old_read) != 1:
        raise ValueError('RBC text input reader changed')
    text = text.replace(old_read, "_read_basic_text(src).splitlines()", 1)
    anchor = 'def _source_program(src: Path, source, kw, fp):'
    if text.count(anchor) != 1:
        raise ValueError('RBC source reader changed')
    text = text.replace(anchor, "def _read_basic_text(src):\n    try:\n        return src.read_text(encoding='utf-8-sig')\n    except UnicodeDecodeError:\n        return src.read_text(encoding='latin-1')\n\n\n" + anchor, 1)
    # The archival listing joins a string variable to THEN without a space.
    anchor = '            if not quoted and not comment and c.isdigit():'
    if text.count(anchor) != 1:
        raise ValueError('RBC token boundary handling changed')
    text = text.replace(anchor, "            if not quoted and not comment and c=='$' and body.startswith('THEN',i+1):\n                chunks.append('$ ');i+=1;continue\n" + anchor, 1)
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

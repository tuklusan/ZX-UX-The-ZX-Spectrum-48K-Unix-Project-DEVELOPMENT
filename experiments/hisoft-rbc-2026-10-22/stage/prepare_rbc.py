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
    new = 'from basic_listing import normalize_listing, split_numbered_line\nfrom line_targets import resolve_missing_targets\nfrom native_scroll import adapt_scroll_counter\nfrom restore_data import resolve_restores\nfrom constant_data import adapt_literal_data\nfrom glyph_data import specialize_glyph_data\nfrom udg_bounds import allow_bounded_udg_loops\nfrom udg_nested import allow_nested_glyph_writes\nfrom udg_chr_bounds import allow_bounded_chr_glyphs\nfrom rom_keyread import allow_key_state_read\nfrom rom_keyboard_control import allow_rom_keyboard_controls\nfrom native_pause_rt import install as install_native_pause\nfrom native_keyread_rt import install as install_native_keyread\nfrom native_val_rt import install as install_native_val\nfrom bss_layout import target_offset\nfrom startup_colors import save_and_set, save_controls, restore, append_slots\nfrom computed_lines import compiler_with_computed_lines\n' + old
    if text.count(old) != 1 or text.count('program = source.tokenize_directives(program,kw)') != 1:
        raise ValueError('RBC checkpoint changed; extension location needs review')
    text = text.replace(old, new, 1)
    old = 'program = source.tokenize_directives(program,kw)'
    text = text.replace(old, old + '\n        program, scroll_lines = adapt_scroll_counter(program, kw)\n        program, next_lines = resolve_missing_targets(program, kw, initial.fp)\n        program, data_lines = resolve_restores(program, kw, initial.fp)\n        program, constant_data_lines = adapt_literal_data(program, kw, initial.fp, source, source.tap)\n        program, glyph_data_lines = specialize_glyph_data(program, kw, initial.fp, source, source.tap)', 1)
    # Confirm bounded glyph writes across numbered FOR/POKE/NEXT lines.
    check_anchor = 'checks = analyze_lines(spectrum_tap.split_lines(program), kw.TOKEN)'
    if text.count(check_anchor) != 1:
        raise ValueError('RBC memory inspection location changed')
    text = text.replace(check_anchor, check_anchor +
                        '\n        allow_bounded_udg_loops(spectrum_tap.split_lines(program), kw.TOKEN, checks)\n        allow_nested_glyph_writes(spectrum_tap.split_lines(program), kw.TOKEN, checks)\n        allow_bounded_chr_glyphs(spectrum_tap.split_lines(program), kw.TOKEN, checks)\n        allow_key_state_read(checks)\n        allow_rom_keyboard_controls(checks)', 1)
    # Try the compiler's in-memory line zero for a missing OPEN.
    # HiSoft needs OPEN before the first user BASIC line.
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
    # Keep numbered blank lines such as 59 Mushroom Invasion's line 8.
    original = (
        "        match=re.match(r'^(\\d+)\\s+(.*)$',raw)\n"
        "        if not match:\n"
        "            raise ValueError(f'{src.name}: invalid BASIC text line {file_line}')\n"
        "        number=int(match.group(1)); body=match.group(2)"
    )
    replacement = (
        "        try:\n"
        "            number, body = split_numbered_line(raw)\n"
        "        except ValueError as exc:\n"
        "            raise ValueError(f'{src.name}: invalid BASIC text line {file_line}') from exc"
    )
    if text.count(original) != 1:
        raise ValueError('RBC text line reader changed; blank line patch needs review')
    text = text.replace(original, replacement, 1)
    text = text.replace("source.tokenize_line(''.join(chunks),kw)",
                        "source.tokenize_line(normalize_listing(''.join(chunks)),kw)", 1)
    upstream = 'compiler, hbcimage, source = _hisoft_modules(frontend)'
    if text.count(upstream) != 1:
        raise ValueError('RBC upstream compiler import changed')
    text = text.replace(upstream, upstream + '\n    install_native_pause(compiler)\n    install_native_keyread(compiler)\n    install_native_val(compiler)', 1)
    # The archival listing joins a string variable to THEN without a space.
    anchor = '            if not quoted and not comment and c.isdigit():'
    if text.count(anchor) != 1:
        raise ValueError('RBC token boundary handling changed')
    text = text.replace(anchor, "            if not quoted and not comment and c=='$' and body.startswith('THEN',i+1):\n                chunks.append('$ ');i+=1;continue\n" + anchor, 1)
    text = text.replace("'memory_policy':memory_policy, 'memory_check':memory_report}",
                        "'memory_policy':memory_policy, 'memory_check':memory_report,\n"
                        "                        'next_line_targets':next_lines, 'scroll_counter_lines':scroll_lines}", 1)
    # The HiSoft variable area follows the compiler's code. RBC inserts
    # font and UDG bytes before the final SSX1 variable area, so correct
    # every compiler relocation into the variable area before packing.
    original_target = 'target=entry_image+(orig-p.base)'
    replacement_target = (
        'target=target_offset(orig,p.base,len(p.code),entry_image,'
        'len(e.code),p.bss)'
    )
    if text.count(original_target) != 1:
        raise ValueError('RBC SSX1 variable relocation changed; review needed')
    text = text.replace(original_target, replacement_target, 1)
    # Retain the upstream line-table/search implementation for computed jumps.
    # Enable it only on the upstream compiler's existing diagnostic.
    exact = (
        '        builds=[]\n'
        '        for n,top in enumerate((ramtop,ramtop-389,ramtop-617)):',
        '            c=compiler.Compiler(img,rom,ramtop=top)\n'
        '            res=c.compile_whole(program)',
    )
    substitutions = (
        '        builds=[]\n'
        '        computed_line_compiler = None\n'
        '        for n,top in enumerate((ramtop,ramtop-389,ramtop-617)):',
        '            c=(computed_line_compiler or compiler.Compiler)(img,rom,ramtop=top)\n'
        '            res=c.compile_whole(program)\n'
        "            if (not res.ok and res.detail == 'computed line number'\n"
        '                    and computed_line_compiler is None):\n'
        '                computed_line_compiler = compiler_with_computed_lines(compiler.Compiler)\n'
        '                c=computed_line_compiler(img,rom,ramtop=top)\n'
        '                res=c.compile_whole(program)',
    )
    for before, after in zip(exact, substitutions):
        if text.count(before) != 1:
            raise ValueError('RBC compiler loop changed; computed lookup needs review')
        text = text.replace(before, after, 1)
    # Initialise the program with the 48K BASIC printer colours, but return
    # the surrounding ZX-UX display defaults when this program exits.
    startup_anchors = (
        ('    call=len(e.code)+1;e.call(0,rel=True)',
         '    color_records = save_and_set(e)\n'
         '    control_records = save_controls(e)\n'
         '    call=len(e.code)+1;e.call(0,rel=True)'),
        ('    e.ldhl(0);e.lda(39);e.call(SYS)',
         '    restore(e, color_records)\n'
         '    restore(e, control_records)\n'
         '    e.ldhl(0);e.lda(39);e.call(SYS)'),
        ('    font_start=len(e.code);e.code.extend(font)',
         '    append_slots(e, color_records)\n'
         '    append_slots(e, control_records)\n'
         '    font_start=len(e.code);e.code.extend(font)'),
    )
    for anchor, replacement in startup_anchors:
        if text.count(anchor) != 1:
            raise ValueError('RBC display startup sequence changed; review needed')
        text = text.replace(anchor, replacement, 1)
    memory = checkpoint / 'rbc' / 'memory_safety.py'
    memory_source = memory.read_text()
    old_target = 'target=_target(address)'
    if memory_source.count(old_target) != 1:
        raise ValueError('RBC memory guard changed; UDG fix needs review')
    memory_source = memory_source.replace(
        old_target, "target=_target(('USR ' if op=='USR' else '') + address)", 1)
    memory.write_text(memory_source)
    shutil.copyfile(extensions / 'basic_listing.py', checkpoint / 'rbc' / 'basic_listing.py')
    shutil.copyfile(extensions / 'line_targets.py', checkpoint / 'rbc' / 'line_targets.py')
    old_pause = checkpoint / 'rbc' / 'pause_zero.py'
    if old_pause.is_file():
        old_pause.unlink()
    shutil.copyfile(extensions / 'bss_layout.py', checkpoint / 'rbc' / 'bss_layout.py')
    shutil.copyfile(extensions / 'startup_colors.py', checkpoint / 'rbc' / 'startup_colors.py')
    shutil.copyfile(extensions / 'computed_lines.py', checkpoint / 'rbc' / 'computed_lines.py')
    shutil.copyfile(extensions / 'native_pause_rt.py', checkpoint / 'rbc' / 'native_pause_rt.py')
    shutil.copyfile(extensions / 'native_scroll.py', checkpoint / 'rbc' / 'native_scroll.py')
    shutil.copyfile(extensions / 'udg_bounds.py', checkpoint / 'rbc' / 'udg_bounds.py')
    shutil.copyfile(extensions / 'udg_nested.py', checkpoint / 'rbc' / 'udg_nested.py')
    shutil.copyfile(extensions / 'udg_chr_bounds.py', checkpoint / 'rbc' / 'udg_chr_bounds.py')
    shutil.copyfile(extensions / 'restore_data.py', checkpoint / 'rbc' / 'restore_data.py')
    shutil.copyfile(extensions / 'constant_data.py', checkpoint / 'rbc' / 'constant_data.py')
    shutil.copyfile(extensions / 'glyph_data.py', checkpoint / 'rbc' / 'glyph_data.py')
    shutil.copyfile(extensions / 'rom_keyread.py', checkpoint / 'rbc' / 'rom_keyread.py')
    shutil.copyfile(extensions / 'rom_keyboard_control.py', checkpoint / 'rbc' / 'rom_keyboard_control.py')
    shutil.copyfile(extensions / 'native_keyread_rt.py', checkpoint / 'rbc' / 'native_keyread_rt.py')
    shutil.copyfile(extensions / 'native_val_rt.py', checkpoint / 'rbc' / 'native_val_rt.py')
    compiler.write_text(text)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: prepare_rbc.py CHECKPOINT_DIR EXTENSIONS_DIR')
    prepare(Path(sys.argv[1]), Path(sys.argv[2]))

#!/usr/bin/env python3
"""Install only ZX-UX boundaries around the preserved pyhsb compiler.

Never edit the upstream pyhsb modules or rewrite a tokenized BASIC statement
for the benefit of a particular game. Unsupported HiSoft constructs must
produce compiler diagnostics, not an invented BASIC implementation.
"""
from __future__ import annotations

from pathlib import Path
import shutil


BOUNDARY = (
    'basic_listing.py', 'rom_syntax.py', 'tape_policy.py',
    'bss_layout.py', 'startup_colors.py',
    'native_pause_rt.py', 'native_keyread_rt.py',
    'native_sysvars_rt.py', 'native_sysvar_policy.py', 'spectrum_sysvars.py',
    'spectrum_fonts.py',
    'poke_policy.py', 'poke_proof.py', 'safety_usr.py',
    'udg_bounds.py', 'udg_nested.py', 'udg_chr_bounds.py',
    'rom_keyread.py', 'rom_keyboard_control.py', 'rom_scroll.py',
)


def prepare(checkpoint: Path, extensions: Path) -> None:
    compiler = checkpoint / 'rbc' / 'rbc.py'
    text = compiler.read_text()

    def change(before: str, after: str) -> None:
        nonlocal text
        if text.count(before) != 1:
            raise ValueError('Preserved RBC checkpoint changed: ' + before[:80])
        text = text.replace(before, after, 1)

    change('from memory_safety import MemoryBlocked, analyze_lines, enforce, summarize',
           'from basic_listing import split_numbered_line, tokenize_preserving_numeric_at\n'
           'from rom_syntax import validate_rom_lines\n'
           'from spectrum_fonts import detect_font_bank\n'
           'from tape_policy import reject_tape_operations\n'
           'from native_pause_rt import install as install_native_pause\n'
           'from native_keyread_rt import install as install_native_keyread\n'
           'from native_sysvars_rt import install as install_native_sysvars\n'
           'from native_sysvar_policy import allow_private_sysvars\n'
           'from udg_bounds import allow_bounded_udg_loops\n'
           'from udg_nested import allow_nested_glyph_writes\n'
           'from udg_chr_bounds import allow_bounded_chr_glyphs\n'
           'from rom_keyread import allow_key_state_read\n'
           'from rom_keyboard_control import allow_rom_keyboard_controls\n'
           'from rom_scroll import allow_rom_screen_scroll\n'
           'from bss_layout import target_offset\n'
           'from startup_colors import save_and_set, save_controls, restore, append_slots\n'
           'from memory_safety import MemoryBlocked, analyze_lines, enforce, summarize')
    change('compiler, hbcimage, source = _hisoft_modules(frontend)',
           'compiler, hbcimage, source = _hisoft_modules(frontend)\n'
           '    install_native_pause(compiler)\n'
           '    install_native_keyread(compiler)\n'
           '    install_native_sysvars(compiler)')

    # Input adapter: preserve the original BASIC bytes and exact keyword
    # boundaries; do not repair spacing, identifier names or expressions.
    change("src.read_text(encoding='latin-1').splitlines()",
           "src.read_text(encoding='ascii').splitlines()")
    change('        raw=raw.strip()\n        if not raw:continue',
           '        if not raw.strip():continue')
    change("        match=re.match(r'^(\\d+)\\s+(.*)$',raw)\n"
           "        if not match:\n"
           "            raise ValueError(f'{src.name}: invalid BASIC text line {file_line}')\n"
           "        number=int(match.group(1)); body=match.group(2)",
           "        try:\n"
           "            number, body = split_numbered_line(raw)\n"
           "        except ValueError as exc:\n"
           "            raise ValueError(f'{src.name}: invalid BASIC text line {file_line}') from exc")
    change("source.tokenize_line(''.join(chunks),kw)",
           "tokenize_preserving_numeric_at(''.join(chunks),source,kw)")
    start = text.index('        # Preserve quoted text and REMs verbatim. Only adjust digit-adjacent')
    end = text.index('        # Replace archival {HH} byte notation', start)
    text = text[:start] + '        encoded=tokenize_preserving_numeric_at(body,source,kw)\n' + text[end:]
    change('        if not source.open_lines(program):',
           '        validate_rom_lines(program, rom)\n'
           '        reject_tape_operations(source.tap.split_lines(program), kw.TOKEN)\n'
           '        if not source.open_lines(program):')
    # HiSoft needs OPEN for standalone listings whose first numbered line
    # has no room for an inserted compiler directive. No BASIC statement is
    # rewritten; the directive belongs to HiSoft, not the user's source.
    change('            program = source.add_directives(program, directives, True, [], kw, initial.fp)',
           "            try:\n"
           "                program = source.add_directives(program, directives, True, [], kw, initial.fp)\n"
           "            except source.SourceError as exc:\n"
           "                if directives or 'no free line numbers' not in str(exc):\n"
           "                    raise\n"
           "                program = source.add_directives(program, [], False,\n"
           "                                                ['0 REM : OPEN #'], kw, initial.fp)")
    change('        checks = analyze_lines(spectrum_tap.split_lines(program), kw.TOKEN)',
           '        font_alias, font_requested = detect_font_bank(spectrum_tap.split_lines(program), kw.TOKEN)\n'
           '        checks = analyze_lines(spectrum_tap.split_lines(program), kw.TOKEN)')
    # Memory policy examines tokens, but never changes control flow or
    # substitutes BASIC statements for the compiler to consume.
    change('checks = analyze_lines(spectrum_tap.split_lines(program), kw.TOKEN)',
           'checks = analyze_lines(spectrum_tap.split_lines(program), kw.TOKEN)\n'
           '        allow_bounded_udg_loops(spectrum_tap.split_lines(program), kw.TOKEN, checks)\n'
           '        allow_nested_glyph_writes(spectrum_tap.split_lines(program), kw.TOKEN, checks)\n'
           '        allow_bounded_chr_glyphs(spectrum_tap.split_lines(program), kw.TOKEN, checks)\n'
           '        allow_key_state_read(checks)\n'
           '        allow_rom_keyboard_controls(checks)\n'
           '        allow_rom_screen_scroll(checks)\n'
           '        allow_private_sysvars(checks)')
    # The generated HiSoft variable area is placed after the ZX-UX runtime,
    # process font, and UDG storage when packing the native SSX image.
    change('target=entry_image+(orig-p.base)',
           'target=target_offset(orig,p.base,len(p.code),entry_image,len(e.code),p.bss)')
    change('    call=len(e.code)+1;e.call(0,rel=True)',
           '    color_records = save_and_set(e)\n'
           '    control_records = save_controls(e)\n'
           '    call=len(e.code)+1;e.call(0,rel=True)')
    change('    e.ldhl(0);e.lda(39);e.call(SYS)',
           '    restore(e, color_records)\n'
           '    restore(e, control_records)\n'
           '    e.ldhl(0);e.lda(39);e.call(SYS)')
    change('    font_start=len(e.code);e.code.extend(font)',
           '    append_slots(e, color_records)\n'
           '    append_slots(e, control_records)\n'
           '    font_start=len(e.code);e.code.extend(font)')

    memory = checkpoint / 'rbc' / 'memory_safety.py'
    source = memory.read_text()
    for before, after in (
        ('target=_target(address)', "target=_target(('USR ' if op=='USR' else '') + address)"),
        ("        return 'system_or_kernel'\n    return 'unknown'",
         "        return 'system_or_kernel' if n < 0x5D00 else 'ordinary_ram'\n    return 'unknown'"),
        ("else:sev,cl='block','unbounded_memory_write'",
         "else:sev,cl='review','programmer_managed_write'"),
    ):
        if source.count(before) != 1:
            raise ValueError('Preserved RBC memory policy changed: ' + before)
        source = source.replace(before, after, 1)
    memory.write_text(source)
    for module in BOUNDARY:
        shutil.copyfile(extensions / module, checkpoint / 'rbc' / module)
    (checkpoint / 'rbc' / 'pause_zero.py').unlink(missing_ok=True)
    compiler.write_text(text)


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        raise SystemExit('usage: prepare_rbc.py CHECKPOINT_DIR EXTENSIONS_DIR')
    prepare(Path(sys.argv[1]), Path(sys.argv[2]))

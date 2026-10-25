#!/usr/bin/env python3
"""Install deterministic ZX-UX boundaries around the preserved pyhsb RBC.

The external input path is completely replaced by the verified upstream
BAS2TAP Python tokenizer, supplied locally, never fetched at compile time.
"""
from __future__ import annotations
from pathlib import Path
import shutil

BOUNDARY = (
    'bas2tap.py', 'bas2tap_syntax.py', 'basic_listing.py', 'rom_syntax.py',
    'tape_policy.py', 'external_io_policy.py', 'bss_layout.py', 'startup_colors.py',
    'native_pause_rt.py', 'native_keyread_rt.py', 'native_sysvars_rt.py', 'native_run_rt.py',
    'native_sysvar_policy.py', 'spectrum_sysvars.py', 'spectrum_fonts.py',
    'poke_policy.py', 'poke_proof.py', 'safety_usr.py', 'udg_bounds.py',
    'udg_nested.py', 'udg_chr_bounds.py', 'spectrum_runtime.py', 'rom_keyread.py',
    'rom_keyboard_control.py', 'rom_scroll.py',
)


def prepare(checkpoint: Path, extensions: Path) -> None:
    compiler = checkpoint / 'rbc' / 'rbc.py'
    text = compiler.read_text()

    def change(before: str, after: str) -> None:
        nonlocal text
        if text.count(before) != 1:
            raise ValueError('RBC checkpoint differs: ' + before[:70])
        text = text.replace(before, after, 1)

    change('from memory_safety import MemoryBlocked, analyze_lines, enforce, summarize',
           'from basic_listing import encode_strict_listing\n'
           'from rom_syntax import validate_rom_lines\n'
           'from spectrum_fonts import detect_font_bank\n'
           'from tape_policy import reject_tape_operations\n'
           'from external_io_policy import reject_external_commands\n'
           'from native_pause_rt import install as install_native_pause\n'
           'from spectrum_runtime import install as install_spectrum_runtime\n'
           'from native_run_rt import install as install_native_run\n'
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

    # Replace the whole BAS reader. A secondary tokenizer, legacy fallback,
    # numeric recoding, or keyword repair must not survive this substitution.
    start = text.index('def _source_program(src: Path, source, kw, fp):')
    end = text.index('\ndef _compile_three(', start)
    replacement = '''def _source_program(src: Path, source, kw, fp):
    """Read external numbered BAS solely through vendored upstream BAS2TAP."""
    if src.suffix.lower() != '.bas':
        raise ValueError('RBC accepts numbered ASCII .bas only')
    try:
        listing = src.read_text(encoding='ascii')
        program = encode_strict_listing(listing)
    except (UnicodeError, ValueError) as exc:
        raise ValueError(f'{src.name}: {exc}') from exc
    return src.stem[:10], program

'''
    text = text[:start] + replacement + text[end:]
    change('compiler, hbcimage, source = _hisoft_modules(frontend)',
           'compiler, hbcimage, source = _hisoft_modules(frontend)\n'
           '    install_native_pause(compiler)\n'
           '    install_spectrum_runtime(compiler)\n'
           '    install_native_keyread(compiler)\n'
           '    install_native_sysvars(compiler)\n'
           '    install_native_run(compiler)')
    change('        if not source.open_lines(program):',
           '        validate_rom_lines(program, rom)\n'
           '        reject_tape_operations(source.tap.split_lines(program), kw.TOKEN)\n'
           '        reject_external_commands(source.tap.split_lines(program), kw.TOKEN)\n'
           '        if not source.open_lines(program):')
    change('            program = source.add_directives(program, directives, True, [], kw, initial.fp)',
           '            try:\n'
           '                program = source.add_directives(program, directives, True, [], kw, initial.fp)\n'
           '            except source.SourceError as exc:\n'
           "                if directives or 'no free line numbers' not in str(exc):\n"
           '                    raise\n'
           '                program = source.add_directives(program, [], False,\n'
           "                                                ['0 REM : OPEN #'], kw, initial.fp)")
    change('checks = analyze_lines(spectrum_tap.split_lines(program), kw.TOKEN)',
           'checks = analyze_lines(spectrum_tap.split_lines(program), kw.TOKEN)\n'
           '        allow_bounded_udg_loops(spectrum_tap.split_lines(program), kw.TOKEN, checks)\n'
           '        allow_nested_glyph_writes(spectrum_tap.split_lines(program), kw.TOKEN, checks)\n'
           '        allow_bounded_chr_glyphs(spectrum_tap.split_lines(program), kw.TOKEN, checks)\n'
           '        allow_key_state_read(checks)\n'
           '        allow_rom_keyboard_controls(checks)\n'
           '        allow_rom_screen_scroll(checks)\n'
           '        allow_private_sysvars(checks)')
    change('        checks = analyze_lines(',
           '        font_alias, font_requested = detect_font_bank(spectrum_tap.split_lines(program), kw.TOKEN)\n'
           '        checks = analyze_lines(')
    change('target=entry_image+(orig-p.base)',
           'target=target_offset(orig,p.base,len(p.code),entry_image,len(e.code),p.bss)')
    change("    e=Emitter()",
           "    saved_stack=p.base+len(p.code)+p.bss-2\n    has_restart_slot=p.bss>=2 and any(\n        site>=2 and p.code[site-2:site]==bytes((0xed,0x7b)) and\n        int.from_bytes(p.code[site:site+2],'little')==saved_stack\n        for site in sites)\n    e=Emitter()")
    change("    entry_image=len(e.code)\n    e.code.extend(p.code)",
           "    shim=None\n    if has_restart_slot:\n        shim=len(e.code)\n        e.emit(0xed,0x73)\n        shim_sp=len(e.code);e.relative(0)\n        e.emit(0xc3)\n        shim_jump=len(e.code);e.relative(0)\n    entry_image=len(e.code)\n    e.code.extend(p.code)")
    change("(call,entry_image+p.entry-p.base)",
           "(call,shim if has_restart_slot else entry_image+p.entry-p.base)")
    change("    reloc=sorted(e.fixups)",
           "    if has_restart_slot:\n        e.fix(shim_sp,len(e.code)+p.bss-2)\n        e.fix(shim_jump,entry_image+p.entry-p.base)\n    reloc=sorted(e.fixups)")
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
            raise ValueError('RBC memory policy checkpoint differs: ' + before)
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
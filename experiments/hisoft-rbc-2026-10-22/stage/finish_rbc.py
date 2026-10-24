"""Finish the checked development RBC compiler after its original setup.

Run after prepare_rbc.py. The current CLI, ROM-fitting and Scuba rewrites
apply only to the temporary copy of the compiler, never the archived BASIC.
"""
from __future__ import annotations

from pathlib import Path
import shutil
from rbc_fit import patched


def finish(checkpoint: Path, extensions: Path) -> None:
    source = checkpoint / 'rbc' / 'rbc.py'
    text = source.read_text()

    def change(before: str, after: str) -> None:
        nonlocal text
        if text.count(before) != 1:
            raise ValueError('RBC source changed; review the extended setup')
        text = text.replace(before, after, 1)

    change('from stellar_charset import adapt_stellar_charset, install as install_stellar_charset',
           'from scuba_charset import adapt_scuba_charset, allow_scuba_font_access, '
           'install as install_scuba_charset, rom_font\n'
           'from stellar_charset import adapt_stellar_charset, install as install_stellar_charset')
    change('        program, scroll_lines = adapt_scroll_counter(program, kw)',
           '        program, scuba_lines = adapt_scuba_charset('
           'program, kw, initial.fp, source, source.tap)\n'
           '        program, scroll_lines = adapt_scroll_counter(program, kw)')
    change('        allow_native_evolution_load(spectrum_tap.split_lines(program), checks)',
           '        allow_native_evolution_load(spectrum_tap.split_lines(program), checks)\n'
           '        allow_scuba_font_access(spectrum_tap.split_lines(program), kw.TOKEN, checks)')
    change('    install_native_run(compiler)',
           '    install_native_run(compiler)\n    install_scuba_charset(compiler)')
    change("'scroll_counter_lines':scroll_lines}",
           "'scroll_counter_lines':scroll_lines, 'scuba_charset_mapping':scuba_lines}")
    # The independently agreed machine-code ban must be enforced after
    # all memory classifiers and safe glyph rewrites, for every CLI mode.
    change('from bss_layout import target_offset',
           'from safety_usr import enforce_numeric_usr\nfrom poke_proof import prove_pokes\nfrom val_guard import guard_val\nfrom bss_layout import target_offset')
    change('        memory_report = summarize(checks)',
           '        poke_proofs = prove_pokes(spectrum_tap.split_lines(program), kw.TOKEN, checks)\n'
           '        enforce_numeric_usr(spectrum_tap.split_lines(program), checks, poke_proofs, kw.TOKEN)\n'
           '        safe_vals = guard_val(spectrum_tap.split_lines(program), kw.TOKEN)\n'
           '        memory_report = summarize(checks)')
    change("'memory_policy':memory_policy, 'memory_check':memory_report,",
           "'memory_policy':memory_policy, 'memory_check':memory_report, 'poke_address_proofs':poke_proofs, 'safe_val_literals':safe_vals,")
    text = patched(text)
    # Original Scuba needs a private font to preserve its printable graphics.
    before = '        ssx,diagnostics=build_ssx(builds,font,rld,args.stack,'
    change(before,
           "        if meta.get('scuba_charset_mapping'):\n"
           "            font = rom_font(args.rom.read_bytes())\n" + before)
    for name in ('scuba_charset.py', 'rbc_fit.py', 'rbc_output.py',
                 'safety_usr.py', 'audit_policy.py', 'poke_proof.py', 'val_guard.py'):
        shutil.copyfile(extensions / name, checkpoint / 'rbc' / name)
    source.write_text(text)


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        raise SystemExit('usage: finish_rbc.py CHECKPOINT_DIR EXTENSIONS_DIR')
    finish(Path(sys.argv[1]), Path(sys.argv[2]))

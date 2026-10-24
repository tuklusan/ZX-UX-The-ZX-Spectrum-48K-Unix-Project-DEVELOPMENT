"""Finish RBC's ZX-UX safety policies, native format and memory limit.

This stage does not rewrite BASIC or alter pyhsb's language implementation.
It operates only on the preserved RBC adapter/SSX packer.
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
            raise ValueError('RBC wrapper checkpoint changed: ' + before[:80])
        text = text.replace(before, after, 1)

    change('from bss_layout import target_offset',
           'from safety_usr import enforce_numeric_usr\n'
           'from poke_policy import apply_poke_policy\n'
           'from poke_proof import prove_pokes\n'
           'from val_guard import guard_val\n'
           'from bss_layout import target_offset')
    change('        memory_report = summarize(checks)',
           '        poke_proofs = prove_pokes(spectrum_tap.split_lines(program), kw.TOKEN, checks)\n'
           '        apply_poke_policy(checks, poke_proofs, font_alias)\n'
           '        enforce_numeric_usr(spectrum_tap.split_lines(program), checks, poke_proofs, kw.TOKEN)\n'
           '        safe_vals = guard_val(spectrum_tap.split_lines(program), kw.TOKEN)\n'
           '        memory_report = summarize(checks)')
    change("'memory_policy':memory_policy, 'memory_check':memory_report}",
           "'memory_policy':memory_policy, 'memory_check':memory_report, "
           "'poke_address_proofs':poke_proofs, 'safe_val_literals':safe_vals, 'private_font_alias':font_alias, 'private_font_requested':font_requested}")
    text = patched(text)
    for module in ('rbc_fit.py', 'rbc_output.py', 'audit_policy.py'):
        shutil.copyfile(extensions / module, checkpoint / 'rbc' / module)
    source.write_text(text)


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        raise SystemExit('usage: finish_rbc.py CHECKPOINT_DIR EXTENSIONS_DIR')
    finish(Path(sys.argv[1]), Path(sys.argv[2]))

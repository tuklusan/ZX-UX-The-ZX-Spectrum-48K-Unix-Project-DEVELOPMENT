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
           'from restore_data import resolve_restores\n'
           'from size_opt import prove_literal_string_bounds\n'
           'from constant_dims import specialize_literal_dims\n'
           'from constant_data import adapt_literal_data\n'
           'from bss_layout import target_offset')
    change('        if not source.open_lines(program):',
           '        size_directives, size_proofs = ([], [])\n'
           '        if not directives and not source.open_lines(program):\n'
           '            size_directives, size_proofs = prove_literal_string_bounds(\n'
           '                program, kw, source.tap.split_lines)\n'
           '        chosen_directives = directives + size_directives\n'
           '        if not source.open_lines(program):')
    change('                program = source.add_directives(program, directives, True, [], kw, initial.fp)',
           '                program = source.add_directives(program, chosen_directives, True, [], kw, initial.fp)')
    change('        if not source.open_lines(program):',
           '        program, constant_dim_proofs = specialize_literal_dims(\n'
           '            program, kw, initial.fp, source, source.tap)\n'
           '        if not source.open_lines(program):')
    change('        program = source.tokenize_directives(program,kw)',
           '        program = source.tokenize_directives(program,kw)\n'
           '        program, restore_remaps = resolve_restores(program, kw, initial.fp)')
    change('        memory_report = summarize(checks)',
           '        poke_proofs = prove_pokes(spectrum_tap.split_lines(program), kw.TOKEN, checks)\n'
           '        apply_poke_policy(checks, poke_proofs, font_alias)\n'
           '        enforce_numeric_usr(spectrum_tap.split_lines(program), checks, poke_proofs, kw.TOKEN)\n'
           '        memory_report = summarize(checks)')
    change("'memory_policy':memory_policy, 'memory_check':memory_report}",
           "'memory_policy':memory_policy, 'memory_check':memory_report, "
           "'poke_address_proofs':poke_proofs, 'private_font_alias':font_alias, 'private_font_requested':font_requested, 'optimized_strings':size_proofs, 'restore_remaps':restore_remaps, 'constant_dimensions':constant_dim_proofs}")
    text = patched(text)
    change('from rbc_output import output_path, memory_required, write_mode',
           'from diagnostics import format_failure, RbcArgumentParser\n'
           'from rbc_output import output_path, memory_required, write_mode')
    change('ap=argparse.ArgumentParser(description=__doc__)',
           'ap=RbcArgumentParser(description=__doc__)')
    change("        print('rbc: '+str(exc),file=sys.stderr)\n        return 1\n    except (ValueError,OSError) as exc:",
           "        print(format_failure(exc,args.source),file=sys.stderr)\n"
           "        return 1\n    except (ValueError,OSError) as exc:")
    change("except (ValueError,OSError) as exc:\n        print('rbc: '+str(exc),file=sys.stderr)",
           "except Exception as exc:\n"
           "        print(format_failure(exc,args.source),file=sys.stderr)")
    for module in ('rbc_fit.py', 'rbc_output.py', 'audit_policy.py', 'diagnostics.py', 'restore_data.py', 'size_opt.py', 'constant_dims.py', 'constant_data.py'):
        shutil.copyfile(extensions / module, checkpoint / 'rbc' / module)
    source.write_text(text)


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        raise SystemExit('usage: finish_rbc.py CHECKPOINT_DIR EXTENSIONS_DIR')
    finish(Path(sys.argv[1]), Path(sys.argv[2]))

"""Run independent BAS/TZX RBC paths and write only untracked local outcomes.

There is never a fallback from a failed TZX conversion to BAS text. Native
success means the frozen ZX-UX linker produced a readable SSX1. All failing
or differing results produce a README, never a substituted or edited binary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from dual_source import convert_tzx


def sha(data):
    return hashlib.sha256(data).hexdigest()


def attempt(source_path, output_path, root, compiler, frontend, tape, revision):
    report = output_path.with_suffix('.json')
    cmd = [sys.executable, str(compiler), str(source_path), '--frontend', str(frontend),
           '--sdk', str(root / 'src/zx-ux-sdk'), '--rom',
           str(root / 'src/zx-ux-sdk/rom/48.rom'), '--tape', str(tape),
           '-o', str(output_path), '--report', str(report)]
    output_path.unlink(missing_ok=True)
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    result = {'source': str(source_path.relative_to(root)) if source_path.is_relative_to(root)
              else str(source_path), 'sha256_input': sha(source_path.read_bytes()),
              'rbc_revision': revision, 'exit_status': proc.returncode,
              'stdout': proc.stdout, 'stderr': proc.stderr,
              'native_linked': False}
    if report.exists():
        try:
            result['compiler_report'] = json.loads(report.read_text())
        except (ValueError, OSError) as exc:
            result['report_error'] = str(exc)
    if proc.returncode == 0 and output_path.is_file():
        try:
            sys.path.insert(0, str(root / 'src/zx-ux-sdk'))
            import rld
            payload = output_path.read_bytes()
            parsed = rld.parse_ssx(payload)
            result.update(native_linked=True, linked_bytes=len(payload), sha256_output=sha(payload),
                          bss_bytes=parsed['bss'], image_bytes=len(parsed['image']),
                          stack_bytes=parsed['stack'])
        except Exception as exc:
            result['exit_status'] = 1
            result['stderr'] += '\nRBC E_NATIVE_LINK: rejected invalid SSX1: ' + str(exc)
            output_path.unlink(missing_ok=True)
    elif proc.returncode == 0:
        result.update(exit_status=1, stderr=result['stderr'] + '\nRBC E_NATIVE_LINK: missing linked SSX1')
    return result


def rejected_conversion(tzx, diagnostic, revision):
    return {'source': str(tzx), 'sha256_input': sha(tzx.read_bytes()),
            'rbc_revision': revision, 'exit_status': 1, 'native_linked': False,
            'stderr': diagnostic, 'stdout': '', 'failure_class': 'TZX conversion/fidelity'}


def outcome_readme(game, bas, tzx, comparison):
    def summary(title, r):
        if r.get('native_linked'):
            return (f'- {title}: linked {r["linked_bytes"]} bytes; SHA-256 '
                    f'{r["sha256_output"]}; exit {r["exit_status"]}.')
        diagnostics = r.get('stderr', '').strip() or r.get('stdout', '').strip() or 'no diagnostic'
        return f'- {title}: failed (exit {r["exit_status"]}); {diagnostics.replace(chr(10), " | ")}'
    return '\n'.join((f'# {game}: RBC Round 2', '',
                      'Independent original BAS and tokenized TZX results using the same RBC revision.',
                      '', summary('BAS', bas), summary('TZX', tzx),
                      f'- Comparison: {comparison["status"]}; {comparison.get("reason", "not byte-identical")}', '')) + '\n'


def run(root, compiler, frontend, tape, workspace, revision):
    import source
    import hbcimage
    from rbc import _source_program
    import rbc

    root, compiler, frontend, tape, workspace = map(Path, (root, compiler, frontend, tape, workspace))
    game_dir = root / 'src/bonus/60-programs'
    work = workspace
    work.mkdir(parents=True, exist_ok=True)
    kw = source.Keywords((root / 'src/zx-ux-sdk/rom/48.rom').read_bytes())
    image = hbcimage.Image.from_tape(tape)
    impl = __import__('compiler')
    fp = impl.Compiler(image, (root / 'src/zx-ux-sdk/rom/48.rom').read_bytes(), ramtop=65367).fp
    games = sorted(p for p in game_dir.iterdir() if p.is_dir() and len(p.name) > 3
                   and p.name[:2].isdigit() and p.name[2] == '-')
    if len(games) != 60:
        raise ValueError(f'expected exactly 60 games, found {len(games)}')
    outcomes = {}
    published = work / 'published'
    for index, folder in enumerate(games, 1):
        game = folder.name
        input_dir = folder / 'BASIC'
        bas, tzx = input_dir / f'{game}.bas', input_dir / f'{game}.tzx'
        if not bas.exists() or not tzx.exists():
            raise ValueError(f'{game}: missing original BAS or TZX')
        slot = work / game
        slot.mkdir(parents=True, exist_ok=True)
        to_bas, to_tzx = slot / 'from-bas.ssx', slot / 'from-tzx.ssx'
        # Independent tape extraction does not need the BAS compile result.
        ascii_copy = slot / 'from-tape' / f'{game}.bas'
        try:
            converter_report = convert_tzx(tzx, bas, ascii_copy, rbc, source, kw, fp)
            converted = True
        except Exception as exc:
            converted = False
            converter_report = {'error': str(exc), 'category': type(exc).__name__}
        bas_result = attempt(bas, to_bas, root, compiler, frontend, tape, revision)
        if converted:
            tzx_result = attempt(ascii_copy, to_tzx, root, compiler, frontend, tape, revision)
            tzx_result['tape_sha256'] = sha(tzx.read_bytes())
            tzx_result['tape_source'] = str(tzx.relative_to(root))
        else:
            tzx_result = rejected_conversion(tzx, converter_report['error'], revision)
            tzx_result['source'] = str(tzx.relative_to(root))
        if bas_result['native_linked'] and tzx_result['native_linked']:
            a, b = to_bas.read_bytes(), to_tzx.read_bytes()
            if a == b:
                comp = {'status': 'identical', 'first_difference': None}
            else:
                first = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), min(len(a), len(b)))
                comp = {'status': 'mismatch', 'first_difference': first,
                        'bas_size': len(a), 'tzx_size': len(b),
                        'bas_sha256': sha(a), 'tzx_sha256': sha(b),
                        'reason': f'first differing byte at offset {first}'}
        else:
            comp = {'status': 'unavailable', 'first_difference': None,
                    'reason': 'at least one path failed or fidelity could not be proved'}
        target_dir = published / game / 'bin'
        target_dir.mkdir(parents=True, exist_ok=True)
        if comp['status'] == 'identical':
            shutil.copyfile(to_bas, target_dir / f'{game}.ssx')
        else:
            (target_dir / 'README.md').write_text(outcome_readme(game, bas_result, tzx_result, comp))
        outcomes[game] = {'bas': bas_result, 'tzx': tzx_result,
                          'conversion': converter_report, 'comparison': comp}
        (slot / 'comparison.json').write_text(json.dumps(outcomes[game], indent=2) + '\n')
        print(f'{index:02d}/60 {game}: BAS={bas_result["exit_status"]}, '
              f'TZX={tzx_result["exit_status"]}, pair={comp["status"]}', flush=True)
    (work / 'results.json').write_text(json.dumps({'rbc_revision': revision, 'results': outcomes}, indent=2) + '\n')
    if sum(len(list((published / g / 'bin').iterdir())) for g in outcomes) != 60:
        raise AssertionError('one published outcome per game was not produced')
    return outcomes


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    for flag in ('root', 'compiler', 'frontend', 'tape', 'workspace', 'revision'):
        ap.add_argument('--' + flag, required=True)
    arg = ap.parse_args()
    run(arg.root, arg.compiler, arg.frontend, arg.tape, arg.workspace, arg.revision)

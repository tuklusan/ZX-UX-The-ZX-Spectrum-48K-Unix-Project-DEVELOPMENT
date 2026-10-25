"""Check four original BASIC/ZX tape pairs with explicit trial-only memory overrides.

Every source is attempted independently and recorded under build/tmp.
Results are not game publication approvals; kernel starts are not gameplay proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
from dual_source import convert_tzx

GAMES = ('16-snap', '20-ambush', '27-picture-pairs', '56-roots')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def attempt(source, out, frontend, tape, limit, system):
    import rld
    import rvm
    cmd = [sys.executable, str(ROOT / 'trial-result/rbc/rbc.py'),
           str(source), '--frontend', str(frontend), '--sdk',
           str(ROOT / 'src/zx-ux-sdk'), '--rom',
           str(ROOT / 'src/zx-ux-sdk/rom/48.rom'), '--tape', str(tape),
           '--max', str(limit), '-o', str(out),
           '--report', str(out.with_suffix('.json'))]
    process = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    result = {'input_sha256': digest(source), 'exit': process.returncode,
              'stdout': process.stdout, 'stderr': process.stderr, 'linked': False}
    if process.returncode != 0 or not out.exists():
        return result
    try:
        content = out.read_bytes()
        image = rld.parse_ssx(content)
        file_size = len(content)
        total = len(image['image']) + image['bss'] + image['stack']
        if max(file_size, total) > limit:
            raise ValueError('Native linked file or reservation exceeds trial limit')
        result.update({'linked': True, 'file_bytes': file_size,
                       'image_bytes': len(image['image']), 'bss_bytes': image['bss'],
                       'stack_bytes': image['stack'], 'reserved_bytes': total,
                       'sha256': hashlib.sha256(content).hexdigest()})
        # The emulator runs the genuine native loader, not a synthetic linker
        # admission check. A successful start is not proof of game completion.
        try:
            vm = rvm.run_kernel(out, frames=320, system=system, cache=True)
            result['kernel'] = {'started': bool(vm.fg and vm.fg.started is not None),
                                'reason': vm.why,
                                'finished': vm.why == 'exit',
                                'process_status': vm.fg.status if vm.why == 'exit' else None}
        except Exception as exc:
            result['kernel'] = {'started': False, 'error': f'{type(exc).__name__}: {exc}'}
    except Exception as exc:
        result.update({'linked': False, 'validation_error': str(exc)})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, default=24000)
    parser.add_argument('--frontend', type=Path, default=ROOT / 'upstream-pyhsb')
    parser.add_argument('--tape', type=Path, default=ROOT / 'trial-result/hisoft48.tap')
    parser.add_argument('--system', type=Path, default=ROOT / 'build/out/ZX-UX.tzx')
    parser.add_argument('--work', type=Path, default=ROOT / 'build/tmp/rbc-gate2-dual')
    args = parser.parse_args()
    if not 12000 < args.max <= 24000:
        raise ValueError('Trial max must exceed 12000 but not 24000 bytes')
    if not args.system.with_name('kernel.json').is_file():
        raise RuntimeError('Native kernel metadata missing')
    if args.system.read_bytes() != (ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise RuntimeError('Native kernel tape differs from preserved release')
    import compiler
    import hbcimage
    import rbc
    import source
    kw = source.Keywords((ROOT / 'src/zx-ux-sdk/rom/48.rom').read_bytes())
    image = hbcimage.Image.from_tape(args.tape)
    fp = compiler.Compiler(image, (ROOT / 'src/zx-ux-sdk/rom/48.rom').read_bytes(),
                           ramtop=65367).fp
    work = args.work
    work.mkdir(parents=True, exist_ok=True)
    results = {}
    for game in GAMES:
        original = ROOT / 'src/bonus/60-programs' / game / 'BASIC'
        bas, tzx = original / (game + '.bas'), original / (game + '.tzx')
        if not bas.is_file() or not tzx.is_file():
            raise RuntimeError(game + ': original source missing')
        folder = work / game
        folder.mkdir(parents=True, exist_ok=True)
        tape_ascii = folder / 'from-tzx.bas'
        converted = None
        try:
            converted = convert_tzx(tzx, bas, tape_ascii, rbc, source, kw, fp)
        except Exception as exc:
            converted = {'error': f'{type(exc).__name__}: {exc}'}
        bas_result = attempt(bas, folder / 'from-bas.ssx', args.frontend,
                             args.tape, args.max, args.system)
        if 'error' not in converted:
            tzx_result = attempt(tape_ascii, folder / 'from-tzx.ssx',
                                 args.frontend, args.tape, args.max, args.system)
        else:
            tzx_result = {'linked': False, 'exit': None,
                          'conversion_error': converted['error']}
        comparison = {'identical': False}
        if bas_result['linked'] and tzx_result['linked']:
            a = (folder / 'from-bas.ssx').read_bytes()
            b = (folder / 'from-tzx.ssx').read_bytes()
            mismatch = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            comparison = {'identical': a == b, 'first_difference': None if a == b else mismatch,
                          'bas_sha256': digest(folder / 'from-bas.ssx'),
                          'tzx_sha256': digest(folder / 'from-tzx.ssx')}
        item = {'bas_source': str(bas.relative_to(ROOT)),
                'tzx_source': str(tzx.relative_to(ROOT)),
                'bas_input_sha256': digest(bas), 'tzx_input_sha256': digest(tzx),
                'max_trial_only': args.max, 'conversion': converted,
                'bas': bas_result, 'tzx': tzx_result, 'comparison': comparison}
        results[game] = item
        print('GATE2_DUAL', game, json.dumps({'bas': {'exit': bas_result['exit'],
                    'linked': bas_result['linked'], 'native': bas_result.get('kernel')},
                    'tzx': {'exit': tzx_result['exit'], 'linked': tzx_result['linked'],
                            'native': tzx_result.get('kernel')},
                    'identical': comparison['identical'], 'conversion': converted},
                    default=str), flush=True)
        (folder / 'outcome.json').write_text(json.dumps(item, indent=2) + '\n')
    (work / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')
    if len(results) != 4:
        raise RuntimeError('Incomplete four-game outcome collection')
    if not all(v['bas']['linked'] and v['tzx']['linked']
               and v['comparison']['identical'] for v in results.values()):
        raise RuntimeError('Gate 2 four-game dual-source proof incomplete; see outcomes')


if __name__ == '__main__':
    main()

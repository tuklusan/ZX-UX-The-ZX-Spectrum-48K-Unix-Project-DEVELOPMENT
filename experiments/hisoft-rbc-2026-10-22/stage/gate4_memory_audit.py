"""Measure real native memory for the original oversized BASIC programs.

All results remain untracked in build/tmp. The published program tree, the
default 12000-byte admission limit, and original source files are unchanged.
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
import rld
import rvm

GAMES = (
    '02-fall-guy', '07-critical-path-analysis', '08-chomper',
    '09-battleships', '11-defend', '13-radio-power', '14-scuba',
    '15-endings', '19-hobday-expenses', '22-top-trainer',
    '32-buzzy-bee', '41-asset-stripper', '46-evolution-3', '58-invaders',
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(original, target, report, optimized, limit, frontend, tape):
    cmd = [
        sys.executable, str(ROOT / 'trial-result/rbc/rbc.py'),
        str(original), '--frontend', str(frontend),
        '--sdk', str(ROOT / 'src/zx-ux-sdk'),
        '--rom', str(ROOT / 'src/zx-ux-sdk/rom/48.rom'),
        '--tape', str(tape), '-o', str(target),
        '--report', str(report),
    ]
    if optimized:
        cmd.append('--upeepz80')
    if limit != 12000:
        cmd.extend(('--max', str(limit)))
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=160)
    row = {'exit': p.returncode, 'stdout': p.stdout[-3000:],
           'stderr': p.stderr[-3000:], 'linked': False}
    if report.is_file():
        try:
            row['report'] = json.loads(report.read_text())
        except (ValueError, OSError) as exc:
            row['report_error'] = str(exc)
    if p.returncode != 0 or not target.is_file():
        return row
    data = target.read_bytes()
    layout = rld.parse_ssx(data)
    total = len(layout['image']) + layout['bss'] + layout['stack']
    if max(total, len(data)) > limit:
        raise RuntimeError('Linked output exceeds requested trial memory limit')
    row.update(linked=True, file_bytes=len(data),
               image_bytes=len(layout['image']), bss_bytes=layout['bss'],
               stack_bytes=layout['stack'], reserved_bytes=total,
               output_sha256=hashlib.sha256(data).hexdigest())
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workspace', type=Path, default=ROOT / 'build/tmp/rbc-gate4')
    ap.add_argument('--frontend', type=Path, default=ROOT / 'upstream-pyhsb')
    ap.add_argument('--tape', type=Path, default=ROOT / 'trial-result/hisoft48.tap')
    ap.add_argument('--system', type=Path, default=ROOT / 'build/out/ZX-UX.tzx')
    ap.add_argument('--games', nargs='+', default=GAMES)
    args = ap.parse_args()
    if len(args.games) != len(set(args.games)):
        raise ValueError('Duplicate game')
    if not args.system.with_name('kernel.json').is_file():
        raise ValueError('Native kernel metadata missing')
    if args.system.read_bytes() != (ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise ValueError('Rebuilt system tape differs from frozen release')
    if len(GAMES) != 14:
        raise AssertionError('Required original memory fitting set changed')

    result = {}
    for game in args.games:
        if game not in GAMES:
            raise ValueError('Game outside the fourteen original oversized inputs')
        original = ROOT / 'src/bonus/60-programs' / game / 'BASIC' / (game + '.bas')
        folder = args.workspace / game
        folder.mkdir(parents=True, exist_ok=True)
        row = {'game': game, 'input_sha256': sha(original)}
        for optimized in (False, True):
            key = 'optimized' if optimized else 'unoptimized'
            case = folder / key
            case.mkdir(exist_ok=True)
            primary = build(original, case / 'default.ssx', case / 'default.json',
                            optimized, 12000, args.frontend, args.tape)
            item = {'default': primary}
            if not primary['linked']:
                item['test_override_24000'] = build(
                    original, case / 'trial.ssx', case / 'trial.json',
                    optimized, 24000, args.frontend, args.tape)
            else:
                # A startup is distinct from completed gameplay.
                try:
                    vm = rvm.run_kernel(case / 'default.ssx', frames=320,
                                        system=args.system, cache=True)
                    item['native'] = {
                        'started': bool(vm.fg and vm.fg.started is not None),
                        'reason': vm.why,
                        'status': vm.fg.status if vm.fg and vm.why == 'exit' else None,
                    }
                except Exception as exc:
                    item['native'] = {'started': False,
                                      'error': f'{type(exc).__name__}: {exc}'}
            row[key] = item
            measured = primary if primary['linked'] else item['test_override_24000']
            print('GATE4', game, key, json.dumps({
                'default_linked': primary['linked'],
                'default_error': primary.get('stderr', '')[-350:],
                'measured_file': measured.get('file_bytes'),
                'measured_total': measured.get('reserved_bytes'),
                'native': item.get('native'),
            }), flush=True)
        result[game] = row
        (folder / 'outcome.json').write_text(json.dumps(row, indent=2) + '\n')
    args.workspace.mkdir(parents=True, exist_ok=True)
    (args.workspace / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print('GATE4_TOTAL', len(result), 'default linked',
          sum(bool(x[m]['default']['linked']) for x in result.values()
              for m in ('unoptimized', 'optimized')), 'of', len(result) * 2)


if __name__ == '__main__':
    main()

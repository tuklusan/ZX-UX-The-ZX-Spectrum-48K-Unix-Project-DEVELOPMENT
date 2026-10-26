"""Bounded native ZX-UX launch test of published RBC programs.

This proves that each selected linked image begins execution under the
rebuilt frozen kernel. It does not claim interactive gameplay verification.
Keep all per-program results outside the committed source tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import rld
import rvm


def run(system: Path, frames: int, offset: int, count: int | None):
    system = system.resolve()
    expected = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
    if not system.is_file() or system.read_bytes() != expected.read_bytes():
        raise ValueError('rebuilt native tape differs from the frozen system')
    if not system.with_name('kernel.json').is_file():
        raise ValueError('native kernel symbols are missing')
    paths = sorted(ROOT.glob('src/bonus/60-programs/*/bin/*.ssx'))
    if not paths or frames < 1 or offset < 0 or count is not None and count < 1:
        raise ValueError('invalid program sample or frame limit')
    sample = paths[offset:offset + count if count is not None else None]
    if not sample:
        raise ValueError('selected game range is empty')
    records = []
    for path in sample:
        binary = path.read_bytes()
        linked = rld.parse_ssx(binary)
        memory = len(linked['image']) + linked['bss'] + linked['stack']
        if max(len(binary), memory) > 12000:
            raise ValueError(path.name + ': native memory limit exceeded')
        runner = rvm.run_kernel(str(path), frames=frames,
                                system=str(system), cache=True)
        job = runner.fg
        if job.started is None:
            raise RuntimeError(path.name + ': linked program never started')
        if job.ended is not None and runner.session.owns_screen(job.pid):
            raise RuntimeError(path.name + ': exited process still owns screen')
        records.append({
            'game': path.parents[1].name,
            'sha256': hashlib.sha256(binary).hexdigest(),
            'file': len(binary), 'image': len(linked['image']),
            'bss': linked['bss'], 'stack': linked['stack'], 'total': memory,
            'started': job.started, 'ended': job.ended,
            'exit': job.status, 'reason': runner.why,
            'gameplay_verified': False,
        })
    return {
        'kernel_sha256': hashlib.sha256(system.read_bytes()).hexdigest(),
        'available_published_ssx': len(paths),
        'sampled': len(records),
        'frames_per_game': frames,
        'native_startups': sum(r['started'] is not None for r in records),
        'gameplay_verified': False,
        'records': records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path,
                        default=ROOT / 'build/out/ZX-UX.tzx')
    parser.add_argument('--frames', type=int, default=120)
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--count', type=int)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'build/tmp/rbc-native-published-smoke.json')
    args = parser.parse_args()
    report = run(args.system, args.frames, args.offset, args.count)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print('GATE7_NATIVE_PUBLISHED_STARTUP', report['native_startups'],
          'of', report['sampled'], 'linked programs')


if __name__ == '__main__':
    main()

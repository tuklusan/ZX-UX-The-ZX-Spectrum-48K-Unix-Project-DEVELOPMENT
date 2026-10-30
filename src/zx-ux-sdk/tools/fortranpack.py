"""Build the shipped FORTRAN corpus with the local ZX-UX SDK."""
from __future__ import annotations
import csv
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def package(source: Path, stage: Path, sdk: Path):
    root = source / 'assets/fortran-src'
    target = stage / 'assets/fortran-src'
    shutil.copytree(root, target)
    output = stage / 'assets/fortran-bin'
    rows = []
    sys.path.insert(0, str(sdk))
    import rld
    import rtap

    corpus = sorted((root / 'corpus').glob('*.f'))
    units = sorted((root / 'separate').glob('*.f'))
    negative = sorted((root / 'negative').glob('*.f'))
    if (len(corpus), len(units), [p.name for p in negative]) != (178, 6, ['f77s_data_bad.f']):
        raise RuntimeError('FORTRAN corpus changed unexpectedly')
    groups = [('main_step', 'main.f', 'step.f'),
              ('math_main', 'math_main.f', 'math_sub.f'),
              ('common_main', 'common_main.f', 'common_sub.f')]
    jobs = [('corpus', p.stem, [p], p.name.startswith('f77s_'), False)
            for p in corpus]
    for name, a, b in groups:
        jobs.append(('separate', name, [root / 'separate' / a,
                                         root / 'separate' / b], True, True))
    for index, (kind, name, files, f77s, separate) in enumerate(jobs, 1):
        folder = output / kind
        ssx = folder / 'ssx' / (name + '.ssx')
        tzx = folder / 'tzx' / (name + '.tzx')
        ssx.parent.mkdir(parents=True, exist_ok=True)
        tzx.parent.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, '-B', str(source / 'zx-ux-sdk/bin/rfortranc'),
               '--sdk', str(sdk), '--std', 'f77s' if f77s else 'zxux',
               '--native', '-o', str(ssx)]
        if separate:
            cmd.append('--separate')
        cmd += list(map(str, files))
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode and not separate:
            # A smaller bytecode/auto-fit image may fit when native does not.
            retry = [a for a in cmd if a != '--native']
            result = subprocess.run(retry, capture_output=True, text=True)
        status = 'FAIL'
        detail = (result.stderr or result.stdout).strip().splitlines()[-1:] or ['compile failed']
        if result.returncode == 0:
            try:
                data = ssx.read_bytes()
                rld.parse_ssx(data)
                if rtap.need(data) > 14000:
                    raise ValueError('exceeds 14000-byte ZX-UX memory ceiling')
                # Unique short cassette names, independent of long source names.
                label = 'F%04d' % index
                header, payload = rtap.records(data, label)
                rtap.write(str(tzx), b'ZXTape!\x1a\x01\x14',
                           [(1000, header), (2000, payload)])
                _, blocks = rtap.tzx_blocks(tzx.read_bytes())
                if len(blocks) != 2 or [b for _, b in blocks] != [header, payload] or \
                        not all(rtap._parity_ok(b) for _, b in blocks):
                    raise ValueError('invalid TZX cassette')
                status, detail = 'PASS', ['SSX/TZX validated']
            except (OSError, ValueError, rld.LinkError, SystemExit) as error:
                detail = [str(error)]
        if status != 'PASS':
            ssx.unlink(missing_ok=True)
            tzx.unlink(missing_ok=True)
        rows.append((kind, name, status, detail[-1].replace('\t', ' ')))
    with tempfile.TemporaryDirectory(prefix='fortran-negative-') as tmp:
        result = subprocess.run([sys.executable, '-B',
            str(source / 'zx-ux-sdk/bin/rfortranc'), '--std', 'f77s',
            '--emit-c', '-o', str(Path(tmp) / 'bad.c'), str(negative[0])],
            capture_output=True, text=True)
        rejected = result.returncode != 0 and 'rfortranc:' in result.stderr
        rows.append(('negative', negative[0].stem,
                     'REJECTED' if rejected else 'FAIL',
                     (result.stderr or result.stdout).strip().splitlines()[-1]
                     if (result.stderr or result.stdout).strip() else 'expected compiler rejection'))
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'results.tsv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream, delimiter='\t')
        writer.writerow(('kind', 'program', 'status', 'detail'))
        writer.writerows(rows)
    if not rejected:
        raise RuntimeError('FORTRAN negative input was not rejected as expected')
    if not all(any(kind == 'corpus' and name == required and status == 'PASS'
                   for kind, name, status, _ in rows)
               for required in ('hello', 'factorial', 'f77s_fmt')):
        raise RuntimeError('FORTRAN baseline programs failed; see results.tsv in staging')
    print('FORTRAN:', sum(r[2] == 'PASS' for r in rows), '/', len(rows) - 1,
          'builds; 1 negative input rejected')
    return len(rows)

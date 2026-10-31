"""Build the curated FORTRAN showcase with the local ZX-UX SDK."""
from __future__ import annotations

import csv
from pathlib import Path
import shutil
import subprocess
import sys

BURKARDT = (
    'f77s_burkadj', 'f77s_burkcopy', 'f77s_burkcum', 'f77s_burkdot',
    'f77s_burkflip', 'f77s_burkgcd', 'f77s_burkl1', 'f77s_burkl2',
    'f77s_burkmean', 'f77s_burkmin', 'f77s_burkmm', 'f77s_burkprime',
    'f77s_burkreal', 'f77s_burkrsrt', 'f77s_burkscale', 'f77s_burksort',
    'f77s_burkvar', 'f77s_burkvec',
)
NUMERICAL = ('bases', 'factorial', 'f77s_machar', 'prime')
FIELDS = ('collection', 'program', 'status', 'detail')


def package(source: Path, stage: Path, sdk: Path):
    root = source / 'assets/fortran-src/showcase'
    srcbase = stage / 'assets/fortran-src/showcase'
    output = stage / 'assets/fortran-bin/showcase'
    rows = []
    sys.path.insert(0, str(sdk))
    import rld
    import rtap

    jobs = [('burkardt', name) for name in BURKARDT] + [('numerical', name) for name in NUMERICAL]
    missing = [name for collection, name in jobs
               if not (root / collection / (name + '.f')).is_file()]
    if missing:
        raise RuntimeError('FORTRAN showcase source(s) missing: ' + ', '.join(missing))
    ssxdir = output / 'ssx'
    tzxdir = output / 'tzx'
    ssxdir.mkdir(parents=True, exist_ok=True)
    tzxdir.mkdir(parents=True, exist_ok=True)
    for index, (collection, name) in enumerate(jobs, 1):
        original = root / collection / (name + '.f')
        dest = srcbase / collection
        dest.mkdir(parents=True, exist_ok=True)
        source_file = dest / original.name
        shutil.copyfile(original, source_file)
        ssx = ssxdir / (name + '.ssx')
        tzx = tzxdir / (name + '.tzx')
        cmd = [
            sys.executable, '-B', str(source / 'zx-ux-sdk/bin/rfortranc'),
            '--sdk', str(sdk), '--std', 'f77s' if name.startswith('f77s_') else 'zxux',
            '--native', '-o', str(ssx), str(source_file),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode:
            result = subprocess.run([arg for arg in cmd if arg != '--native'], capture_output=True, text=True)
        status = 'FAIL'
        detail = (result.stderr or result.stdout).strip().splitlines()[-1:] or ['compile failed']
        if result.returncode == 0:
            try:
                data = ssx.read_bytes()
                rld.parse_ssx(data)
                if rtap.need(data) > 14000:
                    raise ValueError('exceeds 14000-byte ZX-UX memory ceiling')
                label = 'F%04d' % index
                header, payload = rtap.records(data, label)
                rtap.write(str(tzx), b'ZXTape!\x1a\x01\x14', [(1000, header), (2000, payload)])
                _, blocks = rtap.tzx_blocks(tzx.read_bytes())
                if (len(blocks) != 2 or
                        [b for _, b in blocks] != [header, payload] or
                        not all(rtap._parity_ok(b) for _, b in blocks)):
                    raise ValueError('invalid TZX cassette')
                status, detail = 'PASS', ['SSX/TZX validated']
            except (OSError, ValueError, rld.LinkError, SystemExit) as error:
                detail = [str(error)]
        if status != 'PASS':
            ssx.unlink(missing_ok=True)
            tzx.unlink(missing_ok=True)
        rows.append((collection, name, status, detail[-1].replace('\t', ' ')))
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'results.tsv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream, delimiter='\t')
        writer.writerow(FIELDS)
        writer.writerows(rows)
    failures = [f'{collection}/{name}: {detail}' for collection, name, status, detail in rows if status != 'PASS']
    if failures:
        raise RuntimeError('FORTRAN showcase failed: ' + '; '.join(failures))
    print('FORTRAN showcase:', len(rows), 'programs')
    return len(rows)

"""Compile the curated Pascal showcase and stage verified ZX-UX programs."""
from __future__ import annotations

import contextlib
import csv
import io
from pathlib import Path
import shutil
import sys
import tempfile

SDK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SDK))
from rpc.driver import main as rpc_main
import ras
import rld
import rtap

FIELDS = ('collection', 'program', 'compile', 'ras', 'rld', 'ssx', 'tzx', 'status', 'detail')
SHOWCASE = (
    'recovered_course_030_fibonacci_optimized',
    'recovered_course_040_fibonacci_large',
    'recovered_21_fibonacci_array',
)


def package(source: Path, stage: Path):
    root = source / 'assets/pascal-src/positive'
    cases = [root / name / (name + '.pas') for name in SHOWCASE]
    missing = [str(p) for p in cases if not p.is_file()]
    if missing:
        raise ValueError('Missing Pascal showcase source(s): ' + '; '.join(missing))
    srcbase = stage / 'assets/pascal-src/showcase'
    outbase = stage / 'assets/pascal-bin/showcase'
    ssxdir, tzxdir = outbase / 'ssx', outbase / 'tzx'
    ssxdir.mkdir(parents=True)
    tzxdir.mkdir(parents=True)
    library = SDK / 'lib/libc48.ssa'
    archives = [rld.read_archive(library.read_bytes(), str(library))]
    rows = []
    failed = []
    with tempfile.TemporaryDirectory(prefix='zx-ux-pascal-') as tmp:
        asmfile = Path(tmp) / 'case.s'
        for number, pas in enumerate(cases, 1):
            case = pas.stem
            dest = srcbase / case
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(pas, dest / pas.name)
            row = dict.fromkeys(FIELDS, 'SKIP')
            row.update(collection='showcase', program=case, status='FAIL', detail='not attempted')
            errors = io.StringIO()
            asmfile.unlink(missing_ok=True)
            with contextlib.redirect_stderr(errors):
                result = rpc_main(['-S', str(pas), '-o', str(asmfile)])
            message = errors.getvalue().strip() or 'compiler rejected source'
            if result:
                row.update(compile='FAIL', detail=message)
                failed.append(case + ': ' + message)
                rows.append(row)
                continue
            row['compile'] = 'PASS'
            current = 'ras'
            try:
                asm = asmfile.read_text(encoding='ascii')
                obj = ras.assemble_text(asm, str(pas))
                if not obj.startswith(b'SSO1'):
                    raise ValueError('assembler produced invalid SSO1 header')
                row['ras'] = 'PASS'
                current = 'rld'
                exe, _, _, _, _ = rld.link([rld.Obj(obj, str(pas))], archives,
                                            'start', 512, 0)
                row['rld'] = 'PASS'
                current = 'ssx'
                rld.parse_ssx(exe)
                if rtap.need(exe) > 14000:
                    raise ValueError('program exceeds ZX-UX 14000-byte memory limit')
                row['ssx'] = 'PASS'
                current = 'tzx'
                header, payload = rtap.records(exe, 'P%04d' % number)
                tape = Path(tmp) / 'case.tzx'
                rtap.write(str(tape), b'ZXTape!',
                           [(1000, header), (2000, payload)])
                tzx = tape.read_bytes()
                _, blocks = rtap.tzx_blocks(tzx)
                if (len(blocks) != 2 or
                    not all(rtap._parity_ok(block) for _, block in blocks) or
                    blocks[0][1] != header or blocks[1][1] != payload or
                    blocks[1][1][1:-1] != exe or
                    blocks[0][1][2:7] != ('P%04d' % number).encode('ascii')):
                    raise ValueError('cassette content or parity mismatch')
                row['tzx'] = 'PASS'
                (ssxdir / (case + '.ssx')).write_bytes(exe)
                (tzxdir / (case + '.tzx')).write_bytes(tzx)
                row.update(status='PASS', detail='validated relocatable SSX1 and TZX')
            except Exception as err:
                row[current] = 'FAIL'
                row['detail'] = current + ': ' + str(err)
                failed.append(case + ': ' + row['detail'])
            rows.append(row)
    outbase.mkdir(parents=True, exist_ok=True)
    with (outbase / 'results.tsv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter='	')
        writer.writeheader()
        writer.writerows(rows)
    if failed:
        raise RuntimeError('Pascal showcase failed: ' + '; '.join(failed))
    return len(rows)

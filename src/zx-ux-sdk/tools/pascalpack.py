"""Compile every preserved Pascal case and stage verified ZX-UX programs."""
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

FIELDS = ('kind', 'program', 'compile', 'ras', 'rld', 'ssx', 'tzx', 'status', 'detail')


def package(source: Path, stage: Path):
    root = source / 'assets/pascal-src'
    positives = sorted((root / 'positive').glob('*/*.pas'))
    negatives = sorted((root / 'negative').glob('*/*.pas'))
    if (len(positives), len(negatives)) != (145, 70):
        raise ValueError('Pascal corpus must contain exactly 145 positive and 70 negative cases')
    base = stage / 'assets/pascal-bin'
    ssxdir, tzxdir = base / 'positive/ssx', base / 'positive/tzx'
    ssxdir.mkdir(parents=True)
    tzxdir.mkdir(parents=True)
    library = SDK / 'lib/libc48.ssa'
    archives = [rld.read_archive(library.read_bytes(), str(library))]
    rows = []
    failed = []
    seen = set()
    with tempfile.TemporaryDirectory(prefix='zx-ux-pascal-') as tmp:
        asmfile = Path(tmp) / 'case.s'
        for kind, cases in (('positive', positives), ('negative', negatives)):
            for number, pas in enumerate(cases, 1):
                case = pas.stem
                if case in seen:
                    raise ValueError('repeated Pascal case name: ' + case)
                seen.add(case)
                if pas.is_symlink() or pas.parent.is_symlink():
                    raise ValueError('linked Pascal source: ' + str(pas))
                dest = stage / 'assets/pascal-src' / kind / case
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(pas, dest / pas.name)
                row = dict.fromkeys(FIELDS, 'SKIP')
                row.update(kind=kind, program=case, status='FAIL', detail='not attempted')
                errors = io.StringIO()
                asmfile.unlink(missing_ok=True)
                with contextlib.redirect_stderr(errors):
                    result = rpc_main(['-S', str(pas), '-o', str(asmfile)])
                message = errors.getvalue().strip() or 'compiler rejected source'
                if kind == 'negative':
                    required = (pas.parent / 'expected_err.bin').is_file()
                    row['compile'] = 'FAIL' if result else 'PASS'
                    if result:
                        row['status'] = 'REJECTED' if required else 'EXPLORATORY_REJECTED'
                        row['detail'] = message
                    else:
                        row['status'] = 'UNEXPECTED_ACCEPT' if required else 'EXPLORATORY_ACCEPTED'
                        row['detail'] = ('invalid source accepted' if required else
                                         'exploratory source accepted by compiler')
                        if required:
                            failed.append(kind + '/' + case + ': compiler accepted expected-error case')
                    rows.append(row)
                    continue
                if result:
                    row.update(compile='FAIL', detail=message)
                    failed.append(kind + '/' + case + ': ' + message)
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
                    rtap.write(str(tape), b'ZXTape!\x1a\x01\x14',
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
                    failed.append(kind + '/' + case + ': ' + row['detail'])
                rows.append(row)
    base.mkdir(parents=True, exist_ok=True)
    with (base / 'results.tsv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)
    if failed:
        raise RuntimeError('Pascal corpus failed: ' + '; '.join(failed))
    return len(rows)

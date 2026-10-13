#!/usr/bin/env python3
"""ZX-UX validation description.




"""
import argparse
import os
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / 'tests/c48/matrix.json'
REQUIRED = frozenset((600, 608, 613, 615, 622, 625, 626, 751, 753, 759,
                      770, 776, 779, 924, 981, 982, 1041, 1044, 1080, 1086))



# A P1080 pass must originate from the separately executed, approved rcc
# runtime test. This verifies the report against current bytes rather than
# accepting a rewritten ABI matrix row or a host-language test as native proof.
ENV1_INPUTS = frozenset((
    'tests/c48/native_env1_storage_lifetime.c', 'sdk/lib/crt0.asm',
    'sdk/bin/rcc', 'sdk/lib/build.py', 'sdk/rld.py', 'sdk/rtap.py',
    'sdk/rcc/driver.py', 'build/ZX-UX.tzx',
))
TAP2SNA_SHA256 = 'c754087b68897780211e60d062da4831f04e83a72dc15d88a6dab436e2150e8d'
ROM_SHA256 = 'd55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42'


def verify_native_env1(proof, root=ROOT):
    """Check the recorded native runtime result against current files."""
    def ensure(ok, reason):
        if not ok:
            raise ValueError('P1080 native proof: ' + reason)

    def sha_file(relative, digest, size=None):
        ensure(isinstance(relative, str) and not Path(relative).is_absolute() and
               os.pardir not in Path(relative).parts, 'invalid output path')
        path = root / relative
        ensure(path.is_file() and not path.is_symlink(), 'required file missing: ' + relative)
        if size is not None:
            ensure(path.stat().st_size == size, 'file length differs: ' + relative)
        ensure(isinstance(digest, str) and
               hashlib.sha256(path.read_bytes()).hexdigest() == digest,
               'file checksum differs: ' + relative)

    ensure(isinstance(proof, dict), 'invalid native proof record')
    ensure(proof.get('result') == 'PASS' and
           proof.get('case_id') == 'native_env1_storage_lifetime' and
           proof.get('compiler') == 'sdk/bin/rcc --native' and
           proof.get('target') == 'ZX-UX v1 native',
           'incorrect execution identity or result')
    source = proof.get('source')
    ensure(isinstance(source, dict), 'invalid source identifier')
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                         cwd=root, text=True).strip()
        tree = subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'],
                                       cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError('P1080 native proof: Git source identity unavailable') from exc
    ensure(source.get('source_commit') == commit and
           source.get('source_tree') == tree, 'source revision differs')
    source_files = source.get('files')
    ensure(isinstance(source_files, dict) and
           set(source_files) == ENV1_INPUTS, 'source file list differs')
    for relative, digest in source_files.items():
        sha_file(relative, digest)
    link = proof.get('link')
    ensure(isinstance(link, dict), 'invalid link record')
    sha_file('build/c48-env1/env48.ssx', link.get('ssx_sha256'),
             link.get('ssx_bytes'))
    sha_file('sdk/lib/libc48.ssa', link.get('archive_sha256'))
    ensure(all(isinstance(link.get(k), int) for k in
               ('code', 'bss', 'env1_bss_offset', 'native_required_bytes')),
           'invalid native memory values')
    ensure(link['bss'] >= 1 and
           link['code'] <= link['env1_bss_offset'] < link['code'] + link['bss'] and
           0 < link['native_required_bytes'] <= 14000 and
           isinstance(link.get('selected_archive_members'), list) and
           all(isinstance(m, str) and m for m in link['selected_archive_members']) and
           bool(link['selected_archive_members']), 'ENV1 memory interval check failed')
    snapshot = proof.get('native_snapshot')
    ensure(isinstance(snapshot, dict) and
           snapshot.get('tap2sna_sha256') == TAP2SNA_SHA256 and
           snapshot.get('rom_sha256') == ROM_SHA256 and
           snapshot.get('tape_boot_sha256') == source_files['build/ZX-UX.tzx'],
           'ROM and tape identities differ')
    sha_file('build/c48-env1/native-current-tape.z80',
             snapshot.get('snapshot_sha256'))
    for key in ('runtime_build_log_sha256', 'compiler_log_sha256'):
        ensure(isinstance(proof.get(key), str) and
               re.fullmatch('[0-9a-f]{64}', proof[key]) is not None,
               'native execution log digest absent')

    def check_capture(capture, name):
        ensure(isinstance(capture, dict), 'invalid capture record')
        for ext in ('scr', 'png'):
            path = 'build/c48-env1/proof/' + name + '.' + ext
            ensure(capture.get(ext + '_path') == path, 'capture path differs')
            sha_file(path, capture.get(ext + '_sha256'), 6912 if ext == 'scr' else None)
        png = root / capture['png_path']
        ensure(png.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'),
               'image header differs')

    seq = proof.get('sequential')
    ensure(isinstance(seq, list) and len(seq) == 2,
           'foreground invocation count differs')
    for num, record in enumerate(seq, 1):
        ensure(isinstance(record, dict) and record.get('run') == num and
               record.get('outcome') == 'PASS' and
               isinstance(record.get('free_bytes'), int) and
               record['free_bytes'] >= 0 and
               isinstance(record.get('screen_sha256'), str) and
               re.fullmatch('[0-9a-f]{64}', record['screen_sha256']),
               'foreground run record differs')
        check_capture(record.get('capture'), 'sequential-' + str(num))
    concurrent = proof.get('concurrent')
    ensure(isinstance(concurrent, dict) and concurrent.get('result') == 'PASS' and
           concurrent.get('checked_program_pass') is True and
           concurrent.get('holding_program_pass') is True,
           'overlapping run result differs')
    slots = concurrent.get('simultaneous_image_slots')
    ensure(isinstance(slots, dict) and set(slots) == {'hold', 'check'},
           'process slot record differs')
    hold, check = slots['hold'], slots['check']
    ensure(all(isinstance(x, list) and len(x) == 3 and
               all(isinstance(v, int) for v in x) for x in (hold, check)) and
           hold[0] != check[0] and hold[1] != check[1] and
           hold[2] == 90 and check[2] == 65,
           'ENV1 process separation check failed')
    check_capture(concurrent.get('capture'), 'concurrent')
    return True


def assess(matrix, verifier, ix_witness, root=ROOT, env1_proof=None):
    """Review actual recorded cases, source paths and mandatory target gaps."""
    if matrix.get('schema') != 1 or not isinstance(matrix.get('rows'), list):
        raise ValueError('unsupported ABI matrix')
    rows = matrix['rows']
    indexes = [row.get('paragraph') for row in rows]
    if len(rows) != len(REQUIRED) or len(set(indexes)) != len(indexes) or set(indexes) != REQUIRED:
        raise ValueError('ABI matrix inventory is missing or duplicated')
    if verifier.get('backend') != 'both' or verifier.get('summary', {}).get('FAIL') != 0 or verifier.get('summary', {}).get('ERROR') != 0:
        raise ValueError('ZX-UX validation check failed.')
    cases = verifier.get('cases')
    if not isinstance(cases, list) or verifier['summary'].get('PASS') != len(cases):
        raise ValueError('host verifier case inventory differs')
    passed = {case.get('id') for case in cases if case.get('status') == 'PASS'}
    if len(passed) == 0:
        raise ValueError('no passing verifier cases')
    for row in rows:
        if row.get('status') not in ('supported', 'contract', 'partial'):
            raise ValueError('unknown target clause state')
        references = row.get('passing_cases')
        sources = row.get('source_paths')
        if (not isinstance(references, list) or not references or
                not all(isinstance(case, str) and case in passed for case in references)):
            raise ValueError('target row cites an unverified compiler case')
        if not isinstance(sources, list) or not sources:
            raise ValueError('target row has no source references')
        for reference in sources:
            if not isinstance(reference, str):
                raise ValueError('invalid source reference')
            path = Path(reference)
            if path.is_absolute() or '..' in path.parts or not (root / path).is_file():
                raise ValueError('target source reference not found')
        if not isinstance(row.get('finding'), str) or not row['finding'].strip():
            raise ValueError('ZX-UX validation check failed.')
    if not isinstance(ix_witness, dict) or ix_witness.get('name') != 'native_ix_register_preservation_8_cases':
        raise ValueError('independent IX witness is missing')
    frame = root / 'sdk/lib/frame.asm'
    if (ix_witness.get('result') != 'PASS' or ix_witness.get('count') != 8 or
            ix_witness.get('frame_sha256') != hashlib.sha256(frame.read_bytes()).hexdigest() or
            not isinstance(ix_witness.get('cases'), list) or len(ix_witness['cases']) != 8):
        raise ValueError('independent IX witness does not match current frame source')
    combinations = {(case.get('ix'), case.get('stack')) for case in ix_witness['cases']}
    if combinations != {(ix, sp) for ix in (0, 1, 0xA55A, 0xFFFF) for sp in (0xE000, 0xF000)}:
        raise ValueError('independent IX witness cases are incomplete')
    unresolved = [row['paragraph'] for row in rows if
                  row['status'] == 'partial' and row['paragraph'] != 1080]
    # Old host cases and changes to matrix status cannot resolve P1080.
    # Only checked execution of the linked C48 native fixture can do so.
    if env1_proof is None:
        unresolved.append(1080)
    else:
        verify_native_env1(env1_proof, root)
    return {'indexed': len(rows), 'supported': sum(row['status'] == 'supported' for row in rows),
            'contracts': sum(row['status'] == 'contract' for row in rows),
            'unresolved': sorted(unresolved)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--ix-proof', type=Path, required=True)
    p.add_argument('--env1-proof', type=Path, default=None)
    args = p.parse_args()
    result = assess(json.loads(MATRIX.read_text()), json.loads(args.report.read_text()),
                    json.loads(args.ix_proof.read_text()),
                    env1_proof=(json.loads(args.env1_proof.read_text())
                                if args.env1_proof else None))
    print('C48 target rows:', result['indexed'])
    print('Supported:', result['supported'])
    print('Documented contracts:', result['contracts'])
    print('Unresolved target paragraphs:', ', '.join(map(str, result['unresolved'])) or 'none')
    if result['unresolved']:
        print('ZX-UX gate status recorded.')
        return 1
    print('C48 target gate passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

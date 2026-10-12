#!/usr/bin/env python3
"""ZX-UX validation description.




"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / 'tests/c48/matrix.json'
REQUIRED = frozenset((600, 608, 613, 615, 622, 625, 626, 751, 753, 759,
                      770, 776, 779, 924, 981, 982, 1041, 1044, 1080, 1086))


def assess(matrix, verifier, ix_witness, root=ROOT):
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
    unresolved = [row['paragraph'] for row in rows if row['status'] == 'partial']
    # P1080 cannot be closed merely by changing matrix status. The present
    # verifier has no independent native process ENV1 storage witness.
    env = next(row for row in rows if row['paragraph'] == 1080)
    if 'native_env1_storage_lifetime' not in env['passing_cases'] or 'native_env1_storage_lifetime' not in passed:
        if 1080 not in unresolved:
            unresolved.append(1080)
    return {'indexed': len(rows), 'supported': sum(row['status'] == 'supported' for row in rows),
            'contracts': sum(row['status'] == 'contract' for row in rows),
            'unresolved': sorted(unresolved)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--ix-proof', type=Path, required=True)
    args = p.parse_args()
    result = assess(json.loads(MATRIX.read_text()), json.loads(args.report.read_text()),
                    json.loads(args.ix_proof.read_text()))
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

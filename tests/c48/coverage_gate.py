#!/usr/bin/env python3
"""Check C48 clause status records."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / 'docs' / '04-C48 Language Specification Rev 0.11.docx'
TRACE = Path(__file__).with_name('traceability.json')


def assess(trace, run):
    """Check exact one-to-one traceability and the recorded case outcomes."""
    if run.get('spec_sha256') != trace.get('spec_sha256'):
        raise ValueError('specification identity differs')
    if run.get('backend') != 'both':
        raise ValueError('both verifier modes are required')
    cases = run.get('cases')
    clauses = run.get('clauses')
    requirements = trace.get('requirements')
    if not isinstance(cases, list) or not isinstance(clauses, list) or not isinstance(requirements, list):
        raise ValueError('missing verification records')
    expected = {r['paragraph_index']: r for r in requirements}
    actual = {c['paragraph_index']: c for c in clauses}
    if len(expected) != len(requirements) or len(actual) != len(clauses) or expected.keys() != actual.keys():
        raise ValueError('missing or duplicated paragraph records')
    if len(expected) != 759:
        raise ValueError('unexpected specification paragraph count')
    by_id = {}
    for c in cases:
        if c.get('status') != 'PASS':
            raise ValueError('verifier case did not pass')
        if c.get('backend') not in ('native', 'bytecode'):
            raise ValueError('unknown backend')
        by_id.setdefault(c['id'], []).append(c)
        for para in c.get('paragraphs', []):
            if para not in expected:
                raise ValueError('verifier references unknown paragraph')
    if run.get('summary', {}).get('PASS') != len(cases) or run['summary'].get('FAIL') != 0 or run['summary'].get('ERROR') != 0:
        raise ValueError('verifier execution count differs')
    pending = []
    excluded = []
    exercised = 0
    for para, req in expected.items():
        claim = actual[para]
        if claim.get('classification') != req.get('classification'):
            raise ValueError('requirement classification differs')
        tests = claim.get('tests')
        if not isinstance(tests, list) or len(tests) != len(set(tests)):
            raise ValueError('invalid linked test inventory')
        if claim.get('status') == 'EXERCISED':
            if not tests or not all(any(para in c.get('paragraphs', []) for c in by_id.get(name, [])) for name in tests):
                raise ValueError('unsupported passing assertion')
            exercised += 1
        elif claim.get('status') == 'UNTESTED' and not tests:
            if req.get('classification') == 'undefined':
                excluded.append(para)
            else:
                pending.append(para)
        else:
            raise ValueError('unexpected clause status')
    if run['summary'].get('UNTESTED_PARAGRAPHS') != len(pending) + len(excluded):
        raise ValueError('coverage count differs')
    return dict(complete=not pending, required_pending=len(pending),
                undefined_pending=len(excluded), exercised=exercised,
                indexed=len(expected))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    trace = json.loads(TRACE.read_text())
    if hashlib.sha256(SPEC.read_bytes()).hexdigest() != trace.get('spec_sha256'):
        raise ValueError('authoritative specification checksum differs')
    status = assess(trace, json.loads(args.report.read_text()))
    print('C48 paragraphs:', status['indexed'])
    print('Linked assertions:', status['exercised'])
    print('Required C48 pending:', status['required_pending'])
    print('Undefined C48 pending:', status['undefined_pending'])
    if not status['complete']:
        print('RELEASE STOPPED: C48 tests pending')
        return 1
    print('C48 release gate passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

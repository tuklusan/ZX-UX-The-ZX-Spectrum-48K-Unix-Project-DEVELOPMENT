#!/usr/bin/env python3
"""Check C48 clause status records."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / 'docs' / '04-C48 Language Specification Rev 0.11.docx'
TRACE = Path(__file__).with_name('traceability.json')
REVIEW = Path(__file__).with_name('original_220_dispositions.csv')
REVIEW_SHA256 = '5c20f7503d5c64e849bc7484e6cc8c557be7b317d6635adca735bbb66ab2921d'
REVIEW_KIND_SHA256 = '14f550d59006895eddbd43fc6b5e544e81e91caa96e97f8fdfea39ffdbaf6c4a'
TARGET_PARAGRAPHS = frozenset((600, 608, 613, 615, 622, 625, 626, 751,
                               753, 759, 770, 776, 779, 924, 981, 982,
                               1041, 1044, 1080, 1086))
ALLOWED_NONEXEC = frozenset(('documentation_or_governance',
                              'host_rcc_architecture_accepted',
                              'optional_or_internal_mechanism',
                              'outside_portable_behavior'))
REVIEW_COUNTS = {'documentation_or_governance': 54,
                 'host_rcc_architecture_accepted': 34,
                 'optional_or_internal_mechanism': 1,
                 'outside_portable_behavior': 1,
                 'target_runtime_or_format': 20}


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



def assess_reviewed(trace, run, review_rows, target_unresolved=TARGET_PARAGRAPHS):
    """Account for reviewed, non-executable obligations without inventing tests.

    Target rows are resolved only by the separately executed native target gate.
    Its unresolved set is passed from target_gate.assess, not from CSV status.
    """
    base = assess(trace, run)
    requirements = {r['paragraph_index']: r for r in trace['requirements']}
    claims = {c['paragraph_index']: c for c in run['clauses']}
    if len(review_rows) != 220:
        raise ValueError('disposition inventory is not 220 paragraphs')
    reviewed = {}
    categories = Counter()
    nonexec = set()
    target = set()
    for row in review_rows:
        try:
            paragraph = int(row['paragraph'])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError('invalid disposition paragraph') from error
        if paragraph in reviewed or paragraph not in requirements:
            raise ValueError('duplicated or unrecognized reviewed paragraph')
        reviewed[paragraph] = row
        req = requirements[paragraph]
        if row.get('sha256') != req['text_sha256'] or row.get('section') != req['section_title']:
            raise ValueError('disposition does not match the canonical specification')
        if not isinstance(row.get('explanation'), str) or not row['explanation'].strip():
            raise ValueError('missing disposition explanation')
        kind = row.get('disposition')
        claim = claims[paragraph]
        if claim['status'] == 'EXERCISED':
            # The base verifier already checked the links against passing cases.
            if kind != 'linked_passing_assertion' or set(row.get('linked_case_ids', '').split(';')) != set(claim['tests']):
                raise ValueError('executed paragraph disposition conflicts with verifier')
        elif claim['status'] == 'UNTESTED' and req['classification'] == 'required':
            if row.get('linked_case_ids'):
                raise ValueError('unexecuted disposition incorrectly cites a test')
            if kind in ALLOWED_NONEXEC:
                if kind == 'host_rcc_architecture_accepted' and not (
                    'sdk/rcc is the host-side C48 compiler' in row['explanation'] and
                    'no second Windows C48 compiler' in row['explanation']):
                    raise ValueError('host compiler scope citation missing')
                nonexec.add(paragraph)
            elif kind == 'target_runtime_or_format':
                target.add(paragraph)
            else:
                raise ValueError('reviewed disposition cannot be reconciled')
        else:
            raise ValueError('reviewed paragraph status is inconsistent')
        categories[kind] += 1
    frozen_classes = sorted((p, reviewed[p]['disposition']) for p in nonexec | target)
    if hashlib.sha256(json.dumps(frozen_classes, separators=(',', ':')).encode()).hexdigest() != REVIEW_KIND_SHA256:
        raise ValueError('a reviewed clause was reclassified without approval')
    for category, expected in REVIEW_COUNTS.items():
        if categories[category] != expected:
            raise ValueError('reviewed disposition count differs from signed review')
    if len(nonexec) != 90 or target != TARGET_PARAGRAPHS:
        raise ValueError('nonexecuted or target disposition scope changed')
    required_pending = {p for p, claim in claims.items()
                        if claim['status'] == 'UNTESTED' and
                        requirements[p]['classification'] == 'required'}
    if required_pending != nonexec | target:
        raise ValueError('required pending paragraph has no validated disposition')
    unresolved = set(target_unresolved)
    if not unresolved <= target:
        raise ValueError('independent target gate reported unknown requirements')
    return dict(base, complete=not unresolved, required_pending=len(unresolved),
                reviewed_nonexecutable=len(nonexec),
                target_indexed=len(target), target_unresolved=sorted(unresolved))


def independent_target_status(report, proof_path, env1_path=None):
    """Run the strict native target/IX witness gate, not an assertion from CSV."""
    from target_gate import assess as assess_target
    matrix = json.loads((ROOT / 'tests/c48/matrix.json').read_text())
    ix = json.loads(proof_path.read_text())
    native = json.loads(env1_path.read_text()) if env1_path is not None else None
    result = assess_target(matrix, report, ix, env1_proof=native)
    if set(result['unresolved']) - TARGET_PARAGRAPHS:
        raise ValueError('unexpected target verification scope')
    return result['unresolved']

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--env1-proof', type=Path, default=None,
                    help='Actual approved-rcc native ENV1 execution report')
    ap.add_argument('--ix-proof', type=Path, default=None,
                    help='Independent native IX proof from this release build')
    args = ap.parse_args()
    trace = json.loads(TRACE.read_text())
    if hashlib.sha256(SPEC.read_bytes()).hexdigest() != trace.get('spec_sha256'):
        raise ValueError('authoritative specification checksum differs')
    report = json.loads(args.report.read_text())
    proof = args.ix_proof or args.report.parent / 'ix-abi-proof.json'
    # No proof, no target credit. A missing proof is a release blocker.
    if proof.is_file():
        outstanding = independent_target_status(report, proof, args.env1_proof)
    else:
        outstanding = sorted(TARGET_PARAGRAPHS)
    if hashlib.sha256(REVIEW.read_bytes()).hexdigest() != REVIEW_SHA256:
        raise ValueError('reviewed disposition file changed; new owner review required')
    with REVIEW.open(newline='', encoding='utf-8') as file:
        records = list(csv.DictReader(file))
    status = assess_reviewed(trace, report, records, outstanding)
    print('C48 paragraphs:', status['indexed'])
    print('Linked assertions:', status['exercised'])
    print('Verified non-executable dispositions:', status['reviewed_nonexecutable'])
    print('Target/ABI obligations:', status['target_indexed'])
    print('Unresolved target paragraphs:', status['target_unresolved'])
    print('Required C48 pending:', status['required_pending'])
    print('Undefined C48 pending:', status['undefined_pending'])
    if not status['complete']:
        print('INCOMPLETE: native target witnesses not yet established')
        return 1
    print('C48 release gate passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

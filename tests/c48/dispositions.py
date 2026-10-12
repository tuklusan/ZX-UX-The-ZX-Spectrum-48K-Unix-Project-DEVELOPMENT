#!/usr/bin/env python3
"""Produce C48 clause status records."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]


def category(item):
    heading = item['section_title'].lower()
    prefix = item['text_prefix'].lower()
    if item['classification'] == 'undefined':
        return 'undefined'
    if any(w in heading for w in ('diagnostic', 'constraint', 'unsupported', 'reserved', 'preprocess')) or any(w in prefix for w in ('shall reject', 'must reject', 'diagnostic')):
        return 'diagnostic'
    if any(w in heading for w in ('library', 'header', 'function', 'stdio')):
        return 'library'
    if any(w in heading for w in ('runtime', 'target', 'memory', 'abi', 'startup', 'syscall', 'stack', 'process', 'link')):
        return 'target'
    if any(w in heading for w in ('purpose', 'terminology', 'conformance', 'appendix', 'scope')):
        return 'review'
    return 'language'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    trace = json.loads((BASE / 'traceability.json').read_text())
    run = json.loads(args.run.read_text())
    spec = ROOT / 'docs' / '04-C48 Language Specification Rev 0.11.docx'
    assert hashlib.sha256(spec.read_bytes()).hexdigest() == trace['spec_sha256']
    assert run['spec_sha256'] == trace['spec_sha256']
    assert run['backend'] == 'both'
    assert run['summary']['FAIL'] == 0 and run['summary']['ERROR'] == 0
    requirements = {x['paragraph_index']: x for x in trace['requirements']}
    clauses = {x['paragraph_index']: x for x in run['clauses']}
    assert len(requirements) == len(clauses) == 759
    assert requirements.keys() == clauses.keys()
    rows = []
    for index, item in requirements.items():
        clause = clauses[index]
        status = clause['status']
        assert status in ('EXERCISED', 'UNTESTED')
        code = 'linked_pass' if status == 'EXERCISED' else category(item)
        rows.append((index, code, item['text_sha256'], ';'.join(clause['tests'])))
    assert sum(row[1] == 'linked_pass' for row in rows) == sum(
        entry['status'] == 'EXERCISED' for entry in run['clauses'])
    assert sum(row[1] != 'linked_pass' for row in rows) == run['summary']['UNTESTED_PARAGRAPHS']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(('clause', 'status', 'digest', 'cases'))
        writer.writerows(rows)
    print('Rows:', len(rows))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Check approved C48 compiler scope against recorded test results."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from coverage_gate import assess

ROOT = Path(__file__).resolve().parents[2]
TESTS = Path(__file__).resolve().parent
HOST_NOTE = 'sdk/rcc is the host-side C48 compiler'


def verify(report, dispositions):
    trace = json.loads((TESTS/'traceability.json').read_text())
    state = assess(trace, report)
    requirements = {r['paragraph_index']:r for r in trace['requirements']}
    indexed = {r['paragraph_index']:r for r in report['clauses']}
    items = list(csv.DictReader(dispositions.open(newline='')))
    if len(items) != 220 or len({int(r['paragraph']) for r in items}) != 220:
        raise ValueError('original 220 review has changed scope')
    counts=Counter()
    open_compiler=[]
    open_target=[]
    for r in items:
        p = int(r['paragraph'])
        if p not in requirements or r['sha256'] != requirements[p]['text_sha256']:
            raise ValueError('disposition clause checksum differs')
        status = indexed[p]['status']
        kind = r['disposition']
        if status == 'EXERCISED':
            if kind != 'linked_passing_assertion' or not indexed[p]['tests']:
                raise ValueError('linked-assertion audit differs')
        elif status == 'UNTESTED':
            if kind == 'host_rcc_architecture_accepted':
                if HOST_NOTE not in r['explanation'] or 'no second Windows C48 compiler' not in r['explanation']:
                    raise ValueError('missing explicit owner-approved host compiler interpretation')
            elif kind == 'target_runtime_or_format':
                open_target.append(p)
            elif kind == 'additional_compiler_corpus':
                open_compiler.append(p)
            elif kind in ('documentation_or_governance', 'optional_or_internal_mechanism', 'outside_portable_behavior'):
                pass
            else:
                raise ValueError('unapproved untested compiler disposition')
        else:
            raise ValueError('unhandled review state')
        counts[kind]+=1
    if counts['host_rcc_architecture_accepted'] != 34:
        raise ValueError('host architecture paragraph count differs')
    reviewed = set(int(r['paragraph']) for r in items)
    other = [p for p,c in indexed.items() if c['status']=='UNTESTED' and
             requirements[p]['classification'] != 'undefined' and p not in reviewed]
    if other:
        raise ValueError('unreviewed required paragraphs remain')
    return state, counts, open_compiler, open_target



def check_integration_sources(report, target):
    """Validate paragraph references without implying any new execution."""
    items=json.loads((TESTS/'matrix.json').read_text())['rows']
    by_paragraph={x['paragraph']:x for x in items}
    if len(items)!=20 or len(by_paragraph)!=20 or set(by_paragraph)!=set(target):
        raise ValueError('target record inventory mismatch')
    passing={r['id'] for r in report['cases'] if r['status']=='PASS'}
    counts=Counter()
    for item in items:
        if item['status'] not in ('supported','documented','partial'):
            raise ValueError('unexpected record state')
        if not item['passing_cases'] or not item['source_paths']:
            raise ValueError('missing source or test reference')
        if not set(item['passing_cases']) <= passing:
            raise ValueError('a cited assertion did not pass')
        for name in item['source_paths']:
            if '..' in Path(name).parts or not (ROOT/name).is_file():
                raise ValueError('a cited file is unavailable')
        counts[item['status']]+=1
    return counts


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--report',type=Path,required=True)
    ap.add_argument('--dispositions',type=Path,default=TESTS/'original_220_dispositions.csv')
    x=ap.parse_args()
    report=json.loads(x.report.read_text())
    state,counts,compiler,target=verify(report,x.dispositions)
    print('C48 host implementation: sdk/rcc (owner-approved; no second Windows compiler)')
    print('C48 executions passed:',report['summary']['PASS'])
    print('Host architecture paragraphs accepted:',counts['host_rcc_architecture_accepted'])
    print('Compiler-specific pending:',len(compiler),compiler)
    groups=check_integration_sources(report,target)
    print('Target records mapped:', len(target), dict(groups))
    print('Full release coverage pending:',state['required_pending'])
    if compiler:
        print('COMPILER SCOPE STOPPED: remaining direct compiler coverage')
        return 1
    print('C48 scoped host-compiler gate passed; full v1 release gate remains separate')
    return 0

if __name__=='__main__':
    raise SystemExit(main())

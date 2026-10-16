from pathlib import Path
import json
import csv
import hashlib
from collections import Counter
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--report',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
P=Path(__file__).resolve().parents[2]
latest=json.loads(args.report.read_text())
trace=json.loads((P/'tests/c48/traceability.json').read_text())
orig=[12,13,14,15,16,17,18,19,20,21,22,25,26,27,28,29,32,33,34,35,36,57,59,86,88,93,94,113,121,136,141,158,162,196,198,199,200,201,202,203,205,206,215,235,266,267,268,276,277,287,288,330,332,346,351,353,354,387,423,429,434,447,457,534,600,608,613,615,622,624,625,626,699,727,747,751,753,756,758,759,765,767,768,770,776,779,781,785,794,799,800,803,806,808,809,810,813,814,815,816,817,818,819,820,821,822,823,824,825,826,827,828,831,833,836,838,839,842,855,875,883,901,903,909,910,911,912,913,916,917,918,919,920,923,924,926,933,936,937,938,939,940,941,942,943,944,947,948,949,950,951,952,953,954,955,956,957,958,959,962,963,964,965,966,967,968,969,970,971,972,973,974,975,976,977,978,979,980,981,982,983,984,987,988,990,993,995,997,999,1001,1003,1005,1007,1008,1011,1012,1013,1014,1015,1017,1019,1020,1022,1025,1028,1036,1039,1041,1044,1046,1049,1056,1064,1070,1072,1074,1080,1084,1086,1089]
now={x['paragraph_index']:x for x in latest['clauses']}
assert len(orig)==220 and len(now)==759
assert latest['spec_sha256']==trace['spec_sha256']
assert latest['summary']['FAIL']==0 and latest['summary']['ERROR']==0
unverified={p for p in orig if now[p]['status']=='UNTESTED'}
assert len(unverified)<=116
# These are review classifications, never exemptions from the release gate.
groups={
 'documentation_or_governance':set([12,13,14,19,20,21,22,25,26,27,29,32,33,35,36,57,94,215,346,387,429,447,756,758,781,785,803,916,917,923,936,937,938,939,940,941,942,943,944,962,963,984,987,988,990,1011,1012,1013,1014,1015,1017,1019,1020,1046]),
 'host_rcc_architecture_accepted':set([15,17,206,794,799,800,806,808,809,810,813,814,815,817,818,819,820,821,822,823,824,826,827,909,910,911,912,913,947,948,951,958,959,983]),
 'target_runtime_or_format':set([600,608,613,615,622,625,626,751,753,759,770,776,779,924,1041,1044,1080,1086,981,982]),
 'additional_compiler_corpus':set([833,842,855,918,920,968]),
 'outside_portable_behavior':set([457]),
 'optional_or_internal_mechanism':set([205]),
}
from itertools import chain
all_groups=list(chain.from_iterable(groups.values()))
assert len(all_groups)==len(set(all_groups)), 'duplicate audit classification'
assert unverified<=set(all_groups), 'unclassified pending clauses: %s'%sorted(unverified-set(all_groups))
notes={
 'documentation_or_governance':'Normative policy, explanatory example, rule hierarchy, or test-process instruction; no isolated compiler observation establishes the entire statement.',
 'host_rcc_architecture_accepted':'Owner-approved ZX-UX v1 interpretation: sdk/rcc is the host-side C48 compiler; no second Windows C48 compiler is needed for v1. This records implementation scope only; behavior and target checks have separate test records.',
 'target_runtime_or_format':'Requires target calling rules, loader, storage, runtime library, diagnostic-stage, or resource validation separate from host-source acceptance.',
 'additional_compiler_corpus':'Aggregate language coverage requirement; individual positive and negative cases pass but exhaustive coverage is not yet demonstrated.',
 'outside_portable_behavior':'Invalid pointer dereference is outside defined portable behavior; do not manufacture a runtime pass for an invalid access.',
 'optional_or_internal_mechanism':'Permitted implementation technique, not a mandatory semantic output; existing ROM golden tests cover observable values, not internal implementation method.',
}
req={x['paragraph_index']:x for x in trace['requirements']}
rows=[]
for p in orig:
 clause=now[p]
 if clause['status']=='EXERCISED':
  state='linked_passing_assertion';note='At least one named compiler or runtime assertion passes; link does not certify the entire paragraph.'
 else:
  state=next(k for k,v in groups.items() if p in v);note=notes[state]
 rows.append(dict(paragraph=p,sha256=req[p]['text_sha256'],section=req[p]['section_title'],disposition=state,linked_case_ids=';'.join(clause['tests']),explanation=note))
assert Counter(x['disposition'] for x in rows)['linked_passing_assertion']>=104
output=args.output
output.parent.mkdir(parents=True, exist_ok=True)
with output.open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print('Disposition counts:',dict(Counter(x['disposition'] for x in rows)))
print('Rows and checksum:',len(rows),hashlib.sha256(output.read_bytes()).hexdigest())

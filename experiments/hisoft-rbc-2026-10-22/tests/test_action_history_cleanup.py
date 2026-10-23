import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile
import json

p=Path(__file__).resolve().parent.parent/'stage'/'action_history_cleanup.py'
spec=importlib.util.spec_from_file_location('cleaner',p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class CleanupTests(unittest.TestCase):
    def test_selects_latest_completed_candidate(self):
        runs=[{'name':'RBC Python compiler trial','id':4,'status':'completed','conclusion':'success','head_branch':'main'},
              {'name':'RBC Python compiler trial','id':5,'status':'completed','conclusion':'failure','head_branch':'main'},
              {'name':'RBC Python compiler trial','id':6,'status':'completed','conclusion':'success','head_branch':'main'}]
        self.assertEqual([r['id'] for r in m.result_candidates(runs)],[6,5,4])
    def test_fast_fails_on_unknown(self):
        with self.assertRaises(RuntimeError):m.verify_result({'mode':'fast','revision':'abc','expected_inputs':11,'invalid':[], 'inputs':[]},'abc')
    def test_records_failures_without_passing_them(self):
        good={'mode':'fast','revision':'abc','expected_inputs':11,'invalid':[], 'inputs':[{'program':str(i),'ok':True} for i in range(11)]}
        self.assertIs(m.verify_result(good,'abc'),good)
        good['inputs'][0]['ok']=False
        self.assertIs(m.verify_result(good,'abc'),good)
    def test_rollup_only_completed_and_excludes_current(self):
        runs=[{'id':1,'name':'A','status':'completed','conclusion':'success'}, {'id':2,'name':'A','status':'queued','conclusion':None},{'id':3,'name':'B','status':'completed','conclusion':'failure'}]
        data=m.rollup(runs,3,{'source_run':1,'source_sha':'s','passed_inputs':11},16)
        self.assertEqual(data['eligible_completed_runs'],1)
        self.assertEqual(data['workflow_outcomes'][0]['count'],1)
    def test_baseline_requires_121_unique(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/m.BASELINE
            path.parent.mkdir(parents=True)
            with zipfile.ZipFile(path,'w') as z: z.writestr('rbc-60-results-shard-0.json',json.dumps([{'program':'a','ok':True}]))
            with self.assertRaises(RuntimeError): m.verify_baseline(Path(root))

if __name__=='__main__': unittest.main()
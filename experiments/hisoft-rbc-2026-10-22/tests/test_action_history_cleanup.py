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
    def test_cleanup_only_consumed_rbc_and_skipped_tags(self):
        rows=[
            dict(id=10,name='RBC Python compiler trial',status='completed',head_branch='main'),
            dict(id=11,name='RBC Python compiler trial',status='completed',head_branch='main'),
            dict(id=12,name='RBC Python compiler trial',status='in_progress',head_branch='main'),
            dict(id=3,name='Build Spectrum Show BASIC tapes',status='completed'),
            dict(id=4,name='Spectrum listing scan acquisition',status='completed'),
            dict(id=5,name='Spectrum 48K magazine BASIC tape checks',status='completed'),
            dict(id=6,name='Clear processed Actions runs',status='completed'),
            dict(id=7,name='Tag beta 0.1.1',status='completed',conclusion='skipped'),
            dict(id=8,name='Tag beta 0.1.1',status='completed',conclusion='success')]
        chosen=[row['id'] for row in rows if m.is_consumed_run(row,6,10,set())]
        self.assertEqual(chosen,[10,7])
        self.assertFalse(m.is_consumed_run(rows[0],6,10,{10}))
        self.assertTrue(m.is_consumed_run(rows[6],42,10,set()))
        self.assertFalse(m.is_consumed_run(dict(id=1,name='RBC Python compiler trial',status='completed',head_branch='feature'),42,10,set()))

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
    def test_fast_allows_added_original_program_pairs(self):
        report={'mode':'fast','revision':'abc','expected_inputs':13,'invalid':[],
                'inputs':[{'program':str(i),'ok':True} for i in range(13)]}
        self.assertIs(m.verify_result(report,'abc'),report)
        report['expected_inputs']=12
        report['inputs']=report['inputs'][:12]
        with self.assertRaises(RuntimeError): m.verify_result(report,'abc')

    def test_uses_permanent_report_when_no_runs_remain(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            stored=root/m.FAST_RECORD
            stored.parent.mkdir(parents=True)
            body={'mode':'fast','revision':'abc','expected_inputs':13,
                  'invalid':[],'inputs':[{'program':str(i),'ok':True} for i in range(13)]}
            record={'source_run':41,'source_sha':'abc','mode':'fast',
                    'expected_inputs':13,'passed_inputs':13,'result':body}
            stored.write_text(json.dumps(record))
            self.assertEqual(m.read_saved_result(root)['source_run'],41)
            record['passed_inputs']=14
            stored.write_text(json.dumps(record))
            with self.assertRaises(RuntimeError):m.read_saved_result(root)

    def test_separate_permanent_full_result_path(self):
        self.assertNotEqual(m.FAST_RECORD, m.FULL_RECORD)
        self.assertEqual(m.FULL_RECORD.name, 'LATEST-RBC-FULL.json')

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
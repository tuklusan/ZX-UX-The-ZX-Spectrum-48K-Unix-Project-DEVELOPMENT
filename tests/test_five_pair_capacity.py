"""Keep C48 background memory pairings usable after tty isolation."""
from pathlib import Path
import sys
import unittest
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'dist/sdk/bin/py'))
import zxux

class PairCapacity(unittest.TestCase):
    def test_existing_pairings(self):
        for first,second in (('hanoi','queens8'),('mobius','torus'),
                             ('ball','hanoi'),('ball','mobius'),('ball','torus')):
            with self.subTest(pair=(first,second)):
                s=zxux.Session(cache=True)
                s.boot()
                jobs=[]
                for name in (first,second):
                    j=s.launch((R/'dist/assets/c48-bin/ssx'/f'{name}.ssx').read_bytes(),name,(),True)
                    jobs.append(j)
                    s.run_until(lambda:j.started is not None,4000,name+' loaded')
                    s.run_until(lambda:not s.kb.busy(),1000,name+' command typed')
                for _ in range(270):s.step()
                for j in jobs:
                    self.assertIsNotNone(s.slot_of(j.pid),f'{first}+{second}: {j.name} not running')

"""Check native calling rules proof is included in the external release command."""
from pathlib import Path
import unittest
TEXT=(Path(__file__).resolve().parents[1]/'tools/release_v1.py').read_text()
class ReleaseNativeWiring(unittest.TestCase):
    def test_proofs_run_before_gates(self):
        probes=('conformance.py','ix_frame_probe.py','native_env1_v1.py','coverage_gate.py','target_gate.py')
        self.assertEqual(sorted(TEXT.index(s) for s in probes),[TEXT.index(s) for s in probes])
    def test_reports_same_between_steps(self):
        self.assertIn("c48, ix, env =",TEXT)
        self.assertIn("'--ix-proof', ix, '--env1-proof', env",TEXT)
        self.assertIn("'--tap2sna', a.tap2sna",TEXT)
if __name__=='__main__':unittest.main()

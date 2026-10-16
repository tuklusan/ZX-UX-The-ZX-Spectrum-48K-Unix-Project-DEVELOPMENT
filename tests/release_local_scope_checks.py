"""External runner must be short, non-destructive and fail closed."""
from pathlib import Path
import subprocess, sys, unittest
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'tools/release_v1.py'
class LocalReleaseChecks(unittest.TestCase):
    def test_help(self):
        p=subprocess.run([sys.executable,str(SRC),'--help'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0)
        self.assertIn('--fuse-test-command',p.stdout)
        self.assertNotIn('--checker',p.stdout)
    def test_required_fuse(self):
        p=subprocess.run([sys.executable,str(SRC),'--sjasm','sjasm','--tap2sna','tap2sna'],capture_output=True,text=True)
        self.assertEqual(p.returncode,2)
        self.assertIn('--fuse-test-command',p.stderr)
    def test_checker_remains_external(self):
        p=subprocess.run([sys.executable,str(SRC),'--sjasm','sjasm','--tap2sna','tap2sna','--fuse-test-command','fuse','--checker','checker.py'],capture_output=True,text=True)
        self.assertEqual(p.returncode,2)
    def test_never_deletes_release(self):
        text=SRC.read_text()
        for bad in ('shutil.rmtree','clear_verified_release','unlink(', 'rmdir(', 'force=True'):
            self.assertNotIn(bad,text)
    def test_fails_on_each_step(self):
        text=SRC.read_text()
        self.assertIn('subprocess.run(command, cwd=r, check=True)',text)
        for step in ('release/build/build.py','release_*checks.py','test_*beta7.py','conformance.py','ix_frame_probe.py','native_env1_v1.py','coverage_gate.py','target_gate.py','run_migrated_baseline.py','fuse-test-command'):
            self.assertIn(step,text)
    def test_all_reports_outside_release(self):
        text=SRC.read_text()
        self.assertIn("r / 'tests/.work'",text)
        self.assertNotIn("r / 'release' / 'logs'",text)
if __name__=='__main__':unittest.main()

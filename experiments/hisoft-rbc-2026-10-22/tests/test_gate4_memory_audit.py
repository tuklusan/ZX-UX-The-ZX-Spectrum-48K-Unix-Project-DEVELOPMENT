"""The memory audit must exercise the actual RBC default and explicit overrides."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from gate4_memory_audit import build


class Gate4LimitTests(unittest.TestCase):
    def test_default_and_explicit_trial_are_distinct(self):
        with tempfile.TemporaryDirectory() as scratch:
            folder = Path(scratch)
            with patch('gate4_memory_audit.subprocess.run') as run:
                run.return_value = subprocess.CompletedProcess([], 1, '', 'blocked')
                for limit in (14000, 12000, 24000):
                    result = build(folder / 'original.bas', folder / 'out.ssx',
                                   folder / 'report.json', False, limit,
                                   folder / 'frontend', folder / 'tape')
                    self.assertFalse(result['linked'])
                    cmd = run.call_args.args[0]
                    self.assertEqual(cmd.count('--max'), int(limit != 14000))
                    if limit != 14000:
                        self.assertEqual(cmd[cmd.index('--max') + 1], str(limit))


if __name__ == '__main__':
    unittest.main()

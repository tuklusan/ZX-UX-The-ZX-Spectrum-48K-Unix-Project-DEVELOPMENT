"""RB2CT development placeholder checks."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / 'src/zx-ux-sdk'
MESSAGE = 'rb2ct: under development\n'


class Rb2ctPlaceholder(unittest.TestCase):
    def test_entry_points(self):
        with tempfile.TemporaryDirectory() as folder:
            env = dict(os.environ, PYTHONPATH=str(SDK), PYTHONDONTWRITEBYTECODE='1')
            commands = ([sys.executable, '-B', str(SDK / 'bin/rb2ct')],
                        [sys.executable, '-B', '-m', 'rb2ct'])
            for command in commands:
                with self.subTest(command=command):
                    result = subprocess.run(command, cwd=folder, env=env,
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, MESSAGE)
                    self.assertEqual(result.stderr, '')
                    self.assertEqual(list(Path(folder).iterdir()), [])

    def test_preserved_library(self):
        common = SDK / 'rb2ct/ports/c48lib'
        self.assertEqual({p.name for p in common.iterdir()},
                         {'c48lib.h', 'c48lib.asm', 'c48lib-font.asm',
                          'FONT-SOURCE.txt'})
        self.assertFalse((SDK / 'rb2ct/ports/60-programs').exists())
        self.assertFalse((SDK / 'tools/rb2ctpack.py').exists())


if __name__ == '__main__':
    unittest.main()

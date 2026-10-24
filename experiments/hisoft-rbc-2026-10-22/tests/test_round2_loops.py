"""Fail-closed FOR/NEXT tests against actual pyhsb-emitted native output.

These verify that supported Spectrum cases compile through pyhsb.
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'build/tmp/rbc-round2'
COMPILER = WORK / 'current/rbc/rbc.py'
FRONTEND = WORK / 'upstream'
TAPE = WORK / 'hisoft48.tap'
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SDK = ROOT / 'src/zx-ux-sdk'


class Round2Loops(unittest.TestCase):
    def native_compile(self, listing):
        self.assertTrue(COMPILER.is_file(), 'HiSoft RBC not prepared')
        self.assertTrue((FRONTEND / 'compiler.py').is_file(), 'pyhsb checkout absent')
        self.assertTrue(TAPE.is_file(), 'HiSoft compiler tape absent')
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / 'loop.bas'
            target = Path(tmp) / 'loop.ssx'
            input_path.write_text(listing, encoding='ascii')
            argv = [sys.executable, str(COMPILER), str(input_path),
                    '--frontend', str(FRONTEND), '--sdk', str(SDK),
                    '--rom', str(ROM), '--tape', str(TAPE), '-o', str(target)]
            env = dict(os.environ, PYTHONPATH=str(FRONTEND))
            result = subprocess.run(argv, cwd=ROOT, env=env, text=True,
                                    capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue(target.is_file(), 'No linked SSX1')
            self.assertTrue(target.read_bytes().startswith(b'SSX1'))

    def test_paired_for_next_links(self):
        self.native_compile('10 FOR I=1 TO 2\n20 PRINT I\n30 NEXT I\n40 STOP\n')

    def test_missing_static_next_can_still_link(self):
        self.native_compile('10 FOR I=1 TO 2\n20 PRINT I\n30 STOP\n')

    def test_jump_into_next_can_still_link(self):
        self.native_compile('10 GO TO 30\n20 FOR I=1 TO 3\n30 NEXT I\n40 STOP\n')

    def test_modified_counter_and_computed_jump_links(self):
        self.native_compile('10 FOR I=1 TO 3\n20 LET I=I+1\n30 GO TO I*10+20\n40 NEXT I\n50 STOP\n')


if __name__ == '__main__':
    unittest.main()

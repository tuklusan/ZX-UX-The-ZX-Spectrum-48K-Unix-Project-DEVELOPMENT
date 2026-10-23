"""Make oversize failures distinct from unsupported BASIC statements."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'stage'))
from result_classify import classify


class NativeLimitTests(unittest.TestCase):
    def test_distinguishes_native_memory_from_compilation_error(self):
        self.assertEqual(classify('rbc: x.bas needs 15500 bytes of native memory (limit 14000)'),
                         'native-memory-limit')
        self.assertEqual(classify('rbc: Not supported line 8030: RUN argument'),
                         'unsupported-basic')


if __name__ == '__main__':
    unittest.main()

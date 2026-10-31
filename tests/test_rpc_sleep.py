"""Exercise Pascal's ZX-UX timed wait without a source rewrite."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
from rpc.backend import compile_to_asm
from rpc.pascal_compiler.errors import PascalError


class PascalSleep(unittest.TestCase):
    def test_runtime_call(self):
        code = compile_to_asm('program test; begin writeln(4); sleep(100) end.')
        self.assertIn('call _sleep', code)
        self.assertIn('ld hl,100', code)

    def test_available_inside_procedures(self):
        code = compile_to_asm('program test; procedure p; begin sleep(2) end; begin p end.')
        self.assertIn('call _sleep', code)

    def test_invalid_sleep(self):
        cases = ('sleep()', 'sleep(1,2)', 'writeln(sleep(100))')
        for call in cases:
            with self.subTest(call=call), self.assertRaises(PascalError):
                compile_to_asm('program test; begin ' + call + ' end.')

    def test_showcase_sources_are_committed_inputs(self):
        samples = sorted((ROOT / 'src/assets/pascal-src/numerical-analysis').glob('*.pas'))
        self.assertEqual(len(samples), 22)
        for sample in samples:
            self.assertIn('sleep(100);', sample.read_text().lower())


if __name__ == '__main__':
    unittest.main()

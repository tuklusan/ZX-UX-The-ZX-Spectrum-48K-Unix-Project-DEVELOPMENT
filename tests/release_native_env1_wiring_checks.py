"""Check the genuine native ENV1 runner is mandatory before release gates."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class ReleaseNativeWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release=(ROOT/'tools/release_v1.py').read_text()
        cls.syntax=ast.parse(cls.release)

    def test_order_and_required_steps(self):
        markers=['step(\'rom-tape-boot\'', 'step(\'c48-native-env1\'',
                 'step(\'c48-coverage\'', 'step(\'c48-target\'']
        positions=[self.release.index(s) for s in markers]
        self.assertEqual(positions,sorted(positions))
        self.assertEqual(self.release.count("step('c48-native-env1'"),1)

    def test_both_gates_require_exact_native_report(self):
        source=self.release
        for name in ("step('c48-coverage'", "step('c48-target'"):
            block=source[source.index(name):source.index('])',source.index(name))]
            self.assertIn("'--env1-proof'",block)
            self.assertIn("'logs/native-env1-v1.json'",block)

    def test_native_runner_is_checked_tool_and_current_tape(self):
        self.assertIn("'tests/c48/native_env1_v1.py'",self.release)
        self.assertIn("'--tap2sna', str(tape_tool)",self.release)
        self.assertIn("validated_file(BUILD / 'logs/native-env1-v1.json')",self.release)


if __name__=='__main__':
    unittest.main()

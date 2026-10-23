"""Check the small ZX-UX adapter around upstream HiSoft PAUSE emission."""
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'upstream-pyhsb'))
sys.path.insert(0, str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'))
from native_pause_rt import install  # noqa: E402


class BaseMachine:
    def __init__(self):
        self.far = bytearray(128)
        self.de_flags = 0
        self.delegated = []

    def run_emitter(self, n, pc, counting, code_base):
        self.delegated.append((n, pc, counting, code_base))
        return pc + 2


class PauseTests(unittest.TestCase):
    def test_native_runtime_replaces_only_pause_emission(self):
        compiler = types.SimpleNamespace(rtlib=types.SimpleNamespace(Machine=BaseMachine))
        install(compiler)
        machine_type = compiler.rtlib.Machine
        install(compiler)
        self.assertIs(compiler.rtlib.Machine, machine_type)
        m = machine_type()
        self.assertEqual(m.run_emitter(55, 10, False, 0), 55)
        self.assertEqual(bytes(m.far[10:12]), b'\x44\x4d')
        self.assertIn(b'\xcd\xbf\x02', bytes(m.far[10:55]))
        self.assertEqual(m.far[54], 0xC9)
        self.assertEqual(m.run_emitter(54, 20, False, 5), 22)
        self.assertEqual(m.delegated, [(54, 20, False, 5)])

    def test_counting_pass_never_stores_bytes(self):
        compiler = types.SimpleNamespace(rtlib=types.SimpleNamespace(Machine=BaseMachine))
        install(compiler)
        m = compiler.rtlib.Machine()
        self.assertEqual(m.run_emitter(55, 10, True, 0), 55)
        self.assertEqual(m.far, bytearray(128))
        m.de_flags = 1
        self.assertEqual(m.run_emitter(55, 10, False, 0), 55)
        self.assertEqual(m.far, bytearray(128))


if __name__ == '__main__':
    unittest.main()

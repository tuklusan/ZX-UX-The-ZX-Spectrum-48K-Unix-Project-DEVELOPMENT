"""Check the small ZX-UX adapter around upstream HiSoft PAUSE emission."""
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'upstream-pyhsb'))
sys.path.insert(0, str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'))
from native_pause_rt import install, _pause_code  # noqa: E402


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
        self.assertEqual(m.run_emitter(55, 10, False, 0), 56)
        self.assertEqual(bytes(m.far[10:12]), b'\x44\x4d')
        self.assertIn(b'\xcd\xbf\x02', bytes(m.far[10:56]))
        self.assertIn(bytes.fromhex("3a005c3c"),m.far)
        self.assertIn(bytes.fromhex("3a045c3c"),m.far)
        self.assertEqual(m.far[55], 0xC9)
        self.assertEqual(m.run_emitter(54, 20, False, 5), 22)
        self.assertEqual(m.delegated, [(54, 20, False, 5)])

    def test_pause_branches_are_resolved_within_emitted_runtime(self):
        from z80asm import asm
        raw = _pause_code(asm)
        self.assertEqual(len(raw), 46)
        self.assertEqual(raw[-1], 0xC9)
        # There are two exits on KSTATE and both land on the common
        # FLAGS-clear epilogue, not at a memory write or in a literal.
        for pos in (20, 26):
            self.assertEqual(raw[pos], 0x20)  # JR NZ
            self.assertEqual(pos + 2 + (raw[pos + 1] if raw[pos + 1] < 128 else raw[pos + 1] - 256), 37)
        # PAUSE 0 loops at HALT, never decrements zero into 65535.
        self.assertEqual(raw[30], 0x28)  # JR Z
        self.assertEqual(30 + 2 + (raw[31] - 256 if raw[31] > 127 else raw[31]), 10)

    def test_counting_pass_never_stores_bytes(self):
        compiler = types.SimpleNamespace(rtlib=types.SimpleNamespace(Machine=BaseMachine))
        install(compiler)
        m = compiler.rtlib.Machine()
        self.assertEqual(m.run_emitter(55, 10, True, 0), 56)
        self.assertEqual(m.far, bytearray(128))
        m.de_flags = 1
        self.assertEqual(m.run_emitter(55, 10, False, 0), 56)
        self.assertEqual(m.far, bytearray(128))


if __name__ == '__main__':
    unittest.main()

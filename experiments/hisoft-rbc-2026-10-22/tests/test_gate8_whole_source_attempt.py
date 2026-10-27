"""Gate 8 must report unresolved runtime sources instead of a false pass."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
from symbolic_capture import Emission
from gate8_full_source_audit import verify_full_source_native


def assemble(source):
    if source == 'ret':
        return b'\xc9'
    raise ValueError('unexpected mnemonic')


class Gate8Attempt(unittest.TestCase):
    def test_a_complete_source_creates_native_plain_link(self):
        group = (Emission(0, 'instruction', 'ret', b'\xc9',
                          source_site='emit:1'),)
        passes = [SimpleNamespace(code=b'\xc9', base=base, entry=base, bss=0)
                  for base in (0x6000, 0x6100, 0x6200)]
        report = verify_full_source_native([group]*3, passes, [1]*3,
                                           assemble, ras)
        self.assertTrue(report['source_owned'])
        self.assertTrue(report['native_link_verified'])
        self.assertEqual(len(report['plain_sha256']), 64)
        self.assertFalse(report['native_behavior_verified'])

    def test_untyped_runtime_keeps_native_link_unverified(self):
        group = (Emission(0, 'runtime-opaque', 'RT1', b'\xc9'),)
        passes = [SimpleNamespace(code=b'\xc9', base=base, entry=base, bss=0)
                  for base in (0x6000, 0x6100, 0x6200)]
        result = verify_full_source_native([group]*3, passes, [1]*3,
                                           assemble, ras)
        self.assertFalse(result['source_owned'])
        self.assertFalse(result['native_link_verified'])
        self.assertTrue(result['blocker'])
        self.assertFalse(result['native_behavior_verified'])


if __name__ == '__main__':
    unittest.main()

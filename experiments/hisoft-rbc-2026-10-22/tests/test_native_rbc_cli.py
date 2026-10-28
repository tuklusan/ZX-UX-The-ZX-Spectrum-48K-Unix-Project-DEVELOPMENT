"""End-to-end checked BAS -> original three-base Z80 -> ras/rld -> SSX."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
import rld
from native_rbc_cli import compile_native, _check_equal

BRICKLAYER = ROOT / 'src/bonus/60-programs/42-bricklayer/BASIC/42-bricklayer.bas'
CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
READY = all(x.is_file() for x in (
    BRICKLAYER, CHECKPOINT/'rbc.py', CHECKPOINT/'font32.bin',
    FRONTEND/'compiler.py', TAPE, ROM))


class NativeRbcCLI(unittest.TestCase):
    def test_fail_closed_on_byte_difference(self):
        with self.assertRaisesRegex(ValueError, 'offset 1'):
            _check_equal(b'\x00\x01', b'\x00\x02')
        with self.assertRaisesRegex(ValueError, 'offset 2'):
            _check_equal(b'\x00\x01', b'\x00\x01\x02')

    def test_disallow_optimizers_and_unverified_sources(self):
        with self.assertRaisesRegex(ValueError, 'original numbered ASCII'):
            compile_native(ROM, CHECKPOINT, FRONTEND, TAPE, ROM)
        with patch.dict(os.environ, {'RBC_G8_OPTIMIZER': 'no-opt-allowed'}):
            if READY:
                with self.assertRaisesRegex(ValueError, 'optimizer injection'):
                    compile_native(BRICKLAYER, CHECKPOINT, FRONTEND, TAPE, ROM)

    @unittest.skipUnless(READY, 'requires locally reconstructed checked HiSoft inputs')
    def test_real_original_source_byte_exact_native_link(self):
        with tempfile.TemporaryDirectory() as workspace:
            output = Path(workspace) / 'original-native.ssx'
            report_file = Path(workspace) / 'original-native.json'
            process = subprocess.run([
                sys.executable, str(STAGE / 'native_rbc_cli.py'),
                str(BRICKLAYER), '--compiler', str(CHECKPOINT),
                '--frontend', str(FRONTEND), '--tape', str(TAPE),
                '--rom', str(ROM), '-o', str(output),
                '--report', str(report_file)],
                check=False, capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            ssx = output.read_bytes()
            report = json.loads(report_file.read_text())
        info = rld.parse_ssx(ssx)
        self.assertEqual(ssx[:4], b'SSX1')
        self.assertEqual(info['entry'], 0)
        self.assertEqual(report['file'], 6667)
        self.assertEqual(report['image'], 6049)
        self.assertEqual(report['bss'], 366)
        self.assertEqual(report['stack'], 384)
        self.assertEqual(report['relocations'], 594)
        self.assertEqual(report['native_ssx_sha256'],
                         '2da076ca4c4d209c66745fd0cbac4164c35598de23cafa06eeca8e6579528170')
        self.assertTrue(report['native_three_base_source_verified'])
        self.assertTrue(report['native_and_legacy_ssx_byte_identical'])
        self.assertFalse(report['optimizer_used'])
        self.assertFalse(report['loader_execution_tested'])
        self.assertFalse(report['native_gameplay_tested'])


if __name__ == '__main__':
    unittest.main()

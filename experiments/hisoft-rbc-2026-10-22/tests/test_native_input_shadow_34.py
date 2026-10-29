"""Fail-closed 34-game shadow admission without modifying published game data."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

FILE = Path(__file__).with_name('native_input_shadow_34.py')
SPEC = importlib.util.spec_from_file_location('native_input_shadow_34', FILE)
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class ShadowCandidateVerification(unittest.TestCase):
    def test_valid_pair_and_corrupted_candidate_fail_closed(self):
        with tempfile.TemporaryDirectory() as d, patch.object(GATE, 'PAIRS', Path(d)):
            folder = Path(d) / '39-flying-geese'
            folder.mkdir()
            image = b'SSX1-test-only'
            for side in ('bas', 'tzx'):
                (folder / ('from-' + side + '.ssx')).write_bytes(image)
                (folder / (side + '-outcome.json')).write_text(json.dumps({
                    'exit': 0, 'size': len(image),
                    'sha256': hashlib.sha256(image).hexdigest()}))
                (folder / (side + '-report.json')).write_text(json.dumps({
                    'native_linker': 'ras/rld',
                    'native_three_base_source_verified': True,
                    'input_source_bridge_three_base_verified': True,
                    'optimizer_used': False, 'file': len(image), 'total': 100}))
            self.assertEqual(GATE.verify_candidate_pair('39-flying-geese'),
                             folder / 'from-bas.ssx')
            (folder / 'from-tzx.ssx').write_bytes(image + b'X')
            with self.assertRaisesRegex(ValueError, 'invalid'):
                GATE.verify_candidate_pair('39-flying-geese')
            (folder / 'from-tzx.ssx').write_bytes(image)
            report = folder / 'tzx-report.json'
            obj = json.loads(report.read_text())
            obj['native_three_base_source_verified'] = False
            report.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError, 'invalid'):
                GATE.verify_candidate_pair('39-flying-geese')

    def test_missing_outcomes_and_timeout_fail_closed(self):
        with tempfile.TemporaryDirectory() as d, patch.object(GATE, 'PAIRS', Path(d)):
            (Path(d) / '01-minelay').mkdir()
            with self.assertRaisesRegex(ValueError, 'missing'):
                GATE.verify_candidate_pair('01-minelay')
        with tempfile.TemporaryDirectory() as d:
            name, result = GATE.one_child('01-minelay', 0, Path(d))
            self.assertEqual(name, '01-minelay')
            self.assertNotEqual(result, 'DISPLAY CHANGED')
            self.assertTrue((Path(d) / '01-minelay.exit').is_file())


if __name__ == '__main__':
    unittest.main()

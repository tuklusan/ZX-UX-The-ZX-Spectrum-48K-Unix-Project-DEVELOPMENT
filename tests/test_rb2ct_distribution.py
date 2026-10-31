"""Build and package the three preserved manual BASIC-to-C48 ports."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / 'src/zx-ux-sdk'
sys.path[:0] = [str(SDK), str(SDK / 'tools')]
import rld
import rtap
import rb2ctpack
from rb2ct.driver import PORTS, available, build


class Rb2ctDistribution(unittest.TestCase):
    def test_legacy_port_sources_are_present(self):
        self.assertEqual(available(), ['01-minelay', '25-galaxians', '58-invaders'])
        for name in available():
            self.assertEqual(len(list((PORTS / '60-programs' / name / 'C48').glob('*.c'))), 1)

    def test_all_ports_compile_and_package(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp)
            self.assertEqual(rb2ctpack.package(stage), 3)
            for name, stem in (('01-minelay', 'minelay'),
                               ('25-galaxians', 'galaxian'),
                               ('58-invaders', 'invaders')):
                src = stage / 'assets/rb2ct-src/60-programs' / name / 'C48' / (stem + '.c')
                self.assertEqual(src.read_bytes(),
                                 (PORTS / '60-programs' / name / 'C48' / src.name).read_bytes())
                ssx = (stage / 'assets/rb2ct-bin/ssx' / (stem + '.ssx')).read_bytes()
                tape = (stage / 'assets/rb2ct-bin/tzx' / (stem + '.tzx')).read_bytes()
                self.assertTrue(rld.parse_ssx(ssx))
                _, blocks = rtap.tzx_blocks(tape)
                self.assertEqual(len(blocks), 2)
                self.assertEqual([block for _, block in blocks],
                                 list(rtap.records(ssx, stem)))
            self.assertEqual(len(list((stage / 'assets/rb2ct-bin/ssx').glob('*.ssx'))), 3)
            self.assertEqual(len(list((stage / 'assets/rb2ct-bin/tzx').glob('*.tzx'))), 3)

    def test_cli_cannot_claim_unknown_basic_translation(self):
        result = subprocess.run([sys.executable, '-B', str(SDK / 'bin/rb2ct'),
                                 '02-fall-guy'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('no historical C48 hand port', result.stderr)

    def test_cli_can_build_external_hand_port(self):
        with tempfile.TemporaryDirectory() as temp:
            source = PORTS / '60-programs/25-galaxians/C48/galaxian.c'
            ssx, tzx = build(source, PORTS / 'c48lib', Path(temp))
            self.assertTrue(ssx.is_file())
            self.assertTrue(tzx.is_file())


if __name__ == '__main__':
    unittest.main()

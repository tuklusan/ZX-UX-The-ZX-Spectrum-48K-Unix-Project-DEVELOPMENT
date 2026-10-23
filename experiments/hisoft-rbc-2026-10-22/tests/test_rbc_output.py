"""Check RBC output naming and authentic native object round trips."""
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'stage'))
sys.path.insert(0, str(HERE.parents[1] / 'src/zx-ux-sdk'))
from rbc_output import output_path, memory_required, asm_from_ssx, write_mode


class OutputTests(unittest.TestCase):
    def test_defaults_match_rcc(self):
        source = Path('/input/space ship.bas')
        self.assertEqual(output_path(source, None, 'link'), source.with_suffix('.ssx'))
        self.assertEqual(output_path(source, None, 'object'), source.with_suffix('.sso'))
        self.assertEqual(output_path(source, None, 'assembly'), source.with_suffix('.s'))
        self.assertEqual(output_path(source, Path('/tmp/out.ssx'), 'link'), Path('/tmp/out.ssx'))

    def test_required_memory_includes_data_and_stack(self):
        self.assertEqual(memory_required({'image': bytes(100), 'bss': 200, 'stack': 384}, 250), 684)
        self.assertEqual(memory_required({'image': bytes(100), 'bss': 0, 'stack': 100}, 300), 300)

    def test_reject_invalid_relocation(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            asm_from_ssx({'image': bytes([3, 0, 0]), 'bss': 0, 'entry': 0, 'relocs': [0]})
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            asm_from_ssx({'image': bytes(10), 'bss': 0, 'entry': 0, 'relocs': [2, 3]})

    def test_sso_is_a_real_relocatable_object(self):
        import ras, rld
        source = '''    section text
    global start
start:
    ld hl,point
    ld a,0
    ret
point: dw variable
    section bss
variable: ds 40
'''
        obj = ras.assemble_text(source, 'basic.s')
        ssx, *_ = rld.link([rld.Obj(obj, 'basic')], [], 'start', 384, 0)
        parsed = rld.parse_ssx(ssx)
        self.assertEqual(parsed['entry'], 0)
        with tempfile.TemporaryDirectory() as temp:
            t = Path(temp)
            write_mode(t / 'test.s', ssx, 'assembly', rld, ras)
            self.assertIn(b'dw start+', (t / 'test.s').read_bytes())
            write_mode(t / 'test.sso', ssx, 'object', rld, ras)
            rebuilt, *_ = rld.link([rld.Obj((t / 'test.sso').read_bytes(), 'test')], [], 'start', 384, 0)
            a, b = rld.parse_ssx(ssx), rld.parse_ssx(rebuilt)
            self.assertEqual(a['image'], b['image'])
            self.assertEqual(a['relocs'], b['relocs'])
            self.assertEqual(a['bss'], b['bss'])
            self.assertEqual(a['stack'], b['stack'])


if __name__ == '__main__':
    unittest.main()

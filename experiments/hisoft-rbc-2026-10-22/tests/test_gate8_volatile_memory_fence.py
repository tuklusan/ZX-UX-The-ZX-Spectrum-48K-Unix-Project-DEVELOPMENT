"""Full native source fences prevent unsafe optimizer RAM reload deletions."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from gate8_volatile_memory_fence import VolatileFenceError, protect_volatile_reads


def native(text):
    obj = ras.assemble_text(text, 'rbc-fence.s')
    return rld.link([rld.Obj(obj, 'rbc-fence.sso')], [],
                    entry='start', stack=384)[0]


class VolatileSourceFenceTests(unittest.TestCase):
    def test_source_fence_does_not_change_native_bytes_or_loads(self):
        original = ('    section text\n    global start\nstart:\n'
                    '    ld (23692),a\n    ld a,(23692)\n    ret\n')
        fenced = protect_volatile_reads(original)
        self.assertEqual(native(original), native(fenced))
        self.assertIn('__rbc_volatile_read_00000:\n    ld a,(23692)', fenced)
        self.assertEqual(fenced.count('ld a,(23692)'), 1)

    def test_upstream_optimizer_preserves_fenced_reload(self):
        try:
            from upeepz80 import PeepholeOptimizer
        except ImportError:
            self.skipTest('requires externally verified upeepz80')
        original = ('    section text\n    global start\nstart:\n'
                    '    ld (23692),a\n    ld a,(23692)\n    ret\n')
        optimized = PeepholeOptimizer().optimize(protect_volatile_reads(original))
        self.assertIn('ld a,(23692)', optimized)

    def test_data_is_not_treated_as_executable_memory_read(self):
        assembly = ('    section text\n    global start\nstart:\n    ret\n'
                    '    section data\n    defb 1,2\n'
                    '    section bss\n    defs 5\n')
        self.assertEqual(protect_volatile_reads(assembly), assembly)

    def test_ambiguous_label_ownership_fails_closed(self):
        text = ('    section text\n    global start\nstart:\n'
                '__rbc_volatile_read_00000:\n    ld a,(hl)\n    ret\n')
        with self.assertRaisesRegex(VolatileFenceError, 'fence label'):
            protect_volatile_reads(text)


if __name__ == '__main__':
    unittest.main()

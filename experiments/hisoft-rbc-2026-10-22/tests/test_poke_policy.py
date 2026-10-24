import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from poke_policy import apply_poke_policy, ProtectedPoke

class F:
    line=100
    operation='POKE'
    severity='block'
    classification='unbounded_memory_write'

class PokeRules(unittest.TestCase):
    def test_dynamic_allowed(self):
        f=F()
        apply_poke_policy([f],[{'line':100,'addresses':[]}])
        self.assertEqual(f.severity,'review')
    def test_screen_allowed(self):
        f=F()
        apply_poke_policy([f],[{'line':100,'addresses':[{'space':'absolute','offset':16384}]}])
        self.assertEqual(f.severity,'review')
    def test_known_kernel_blocked(self):
        for addr in (0,0x5b00,0xffff):
            with self.subTest(addr=addr),self.assertRaises(ProtectedPoke):
                apply_poke_policy([F()],[{'line':100,'addresses':[{'space':'absolute','offset':addr}]}])
    def test_virtual_font_bank_only_allows_private_1024_bytes(self):
        for offset in (60256,60512,61279):
            with self.subTest(offset=offset):
                f=F()
                apply_poke_policy([f],[{'line':100,'addresses':[{'space':'absolute','offset':offset}]}],60256)
                self.assertEqual(f.severity,'review')
        for offset in (60255,61280,0xffff):
            with self.subTest(offset=offset),self.assertRaises(ProtectedPoke):
                apply_poke_policy([F()],[{'line':100,'addresses':[{'space':'absolute','offset':offset}]}],60256)

    def test_virtual_chars_registers_are_not_kernel_writes(self):
        for addr in (23606,23607):
            f=F()
            apply_poke_policy([f],[{'line':100,'addresses':[{'space':'absolute','offset':addr}]}])
            self.assertEqual(f.severity,'info')

    def test_bounded_udg(self):
        for addr in (0,167):
            f=F()
            apply_poke_policy([f],[{'line':100,'addresses':[{'space':'process_udg','offset':addr}]}])
            self.assertEqual(f.severity,'info')
    def test_out_of_bound_udg_blocked(self):
        with self.assertRaises(ProtectedPoke):
            apply_poke_policy([F()],[{'line':100,'addresses':[{'space':'process_udg','offset':168}]}])

if __name__=='__main__':unittest.main()
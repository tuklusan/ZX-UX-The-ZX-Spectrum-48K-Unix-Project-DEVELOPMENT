"""Compiler-side type and process UDG write regression checks."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from safe_usr_rt import UDG_POKE_CHECK, install
from native_sysvars_rt import POKE_RT


class NativeUsr(unittest.TestCase):
    def make(self, address_type, value_type=None):
        class RT:
            USR_UDG = 11
        class Compiler:
            _zxux_sysvars = True
            t = None
            def __init__(self):
                self.emitted=[]; self.rt=[]; self.index=0
            def operand(self):
                self.t = address_type
            def not_supported(self, why):
                raise ValueError(why)
            def call_rt(self, routine):
                self.rt.append(routine)
            def emit(self, text):
                self.emitted.append(text)
            def expr_int(self):
                self.index += 1
                if self.index == 1:
                    self.fn_usr()
                elif value_type is not None:
                    self.t = value_type
            def next_char(self):
                pass
        from types import SimpleNamespace
        API=SimpleNamespace(STRING=3, POSINT=4, RT=RT, Compiler=Compiler)
        install(API)
        return API.Compiler()

    def test_literal_or_computed_string_uses_rom_graphics_service(self):
        c=self.make(3)
        c.fn_usr()
        self.assertEqual(c.rt,[11])
        self.assertEqual(c.t,4)

    def test_dynamic_numeric_usr_still_rejected(self):
        c=self.make(4)
        with self.assertRaisesRegex(ValueError,'numeric USR'):
            c.fn_usr()
        self.assertEqual(c.rt,[])

    def test_poke_with_computed_graphics_pointer_is_guarded(self):
        c=self.make(3)
        c.st_poke()
        self.assertEqual(c.emitted,[UDG_POKE_CHECK, 'push hl','ld e,l; pop hl'])
        self.assertEqual(c.rt,[11,POKE_RT])

    def test_poke_numeric_usr_fails_before_write(self):
        c=self.make(4)
        with self.assertRaisesRegex(ValueError,'numeric USR'):
            c.st_poke()
        self.assertEqual(c.rt,[])

    def test_unrelated_poke_is_not_redirected_to_udg(self):
        c=self.make(3)
        c.expr_int=lambda: None
        c.st_poke()
        self.assertEqual(c.emitted,['push hl','ld e,l; pop hl'])
        self.assertEqual(c.rt,[POKE_RT])

    def test_runtime_guard_rejects_underflow_overflow(self):
        self.assertIn('sbc hl,de',UDG_POKE_CHECK)
        self.assertIn('cp 168',UDG_POKE_CHECK)
        self.assertNotIn('rst 8',UDG_POKE_CHECK)
        self.assertIn('ld a,39; call $6003',UDG_POKE_CHECK)
        self.assertIn('ld hl,11; ld a,1; jp $6003',UDG_POKE_CHECK)
        self.assertIn('pop hl',UDG_POKE_CHECK)

    def test_incompatible_poke_is_not_overwritten(self):
        class Compiler: pass
        from types import SimpleNamespace
        API=SimpleNamespace(Compiler=Compiler)
        with self.assertRaisesRegex(ValueError,'protected-memory'):
            install(API)


if __name__=='__main__':
    unittest.main()

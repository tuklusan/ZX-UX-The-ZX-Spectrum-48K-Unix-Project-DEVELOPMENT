"""Bounded tests for native BASIC RUN compilation and stack handling."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from native_run_rt import install, _uses_run


class FakeCompiler:
    def __init__(self, size=20):
        self.size = size
        self.calls = []
        self.pass0 = 0
        self.line_no = 1
    def reset(self, program):
        self.lines = list(program)
        self.pc = self.vars_start = 100
    def layout_vars(self):
        self.pc = self.vars_start + self.size
    def entry_point_line(self):
        self.calls.append(('entry',))
    @property
    def dispatch(self):
        return {}
    def at_end(self):
        return self.end
    def not_supported(self, detail):
        raise ValueError(detail)
    def emit_op_reloc(self, op, addr):
        self.calls.append(('rel', op, addr))
    def ld_hl(self, arg):
        self.calls.append(('hl', arg))
    def ld_bc_abs(self, arg):
        self.calls.append(('bc', arg))
    def emit(self, asm):
        self.calls.append(('asm', asm))
    def call_rt(self, routine):
        self.calls.append(('rt', routine))
    def emit_restore(self):
        self.calls.append(('restore',))
    def emit_goto(self, op, target):
        self.calls.append(('goto', op, target))


class Module:
    Compiler = FakeCompiler
    class RT:
        MEM_FILL = 55


class RunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install(Module)

    def test_only_real_run_tokens(self):
        self.assertTrue(_uses_run([(1, b'\xfa A=1\xcb\xf7\r')]))
        self.assertFalse(_uses_run([(1, b'\xea\xf7\r')]))
        self.assertFalse(_uses_run([(1, b'"\xf7"\r')]))
        self.assertFalse(_uses_run([(1, b'10\x0e\x00\x00\xf7\x00\x00\r')]))

    def test_restart_clears_users_without_erasing_saved_sp(self):
        obj = Module.Compiler(40)
        obj.reset([(0, b'\xea\r'), (10, b'\xf7\r')])
        obj.layout_vars()
        self.assertEqual((obj._zxux_run_sp, obj._zxux_run_clear_bytes, obj.pc), (140,40,142))
        obj.line_no = 10
        obj.entry_point_line()
        self.assertIn(('rel', 'ld (nn),sp', 140), obj.calls)
        obj.end = True
        obj.st_run()
        self.assertEqual(obj.calls[-7:], [
            ('rel','ld sp,(nn)',140),('hl',100),('bc',39),
            ('asm','ld a,0'),('rt',55),('restore',),('goto','jp nn',10)])

    def test_zero_user_storage_uses_single_safe_byte(self):
        obj = Module.Compiler(0)
        obj.reset([(1, b'\xf7\r')])
        obj.layout_vars()
        self.assertEqual((obj._zxux_run_sp,obj._zxux_run_clear_bytes,obj.pc),(101,1,103))

    def test_other_programs_unchanged(self):
        obj = Module.Compiler(25)
        obj.reset([(1, b'\xf5"RUN"\r')])
        obj.layout_vars()
        obj.entry_point_line()
        self.assertEqual(obj.pc, 125)
        self.assertEqual(obj.calls, [('entry',)])

    def test_run_arguments_rejected(self):
        obj = Module.Compiler(12)
        obj.reset([(1, b'\xf7 100\r')])
        obj.layout_vars()
        obj.end = False
        with self.assertRaisesRegex(ValueError, 'RUN argument'):
            obj.st_run()

    def test_install_is_repeatable(self):
        cls = Module.Compiler
        first = cls.st_run
        install(Module)
        self.assertIs(cls.st_run, first)
        self.assertIn(0xf7, cls().dispatch)

if __name__ == '__main__':
    unittest.main()

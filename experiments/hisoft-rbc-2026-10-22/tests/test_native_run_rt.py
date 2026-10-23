"""Bounded tests for native BASIC RUN compilation and stack handling."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from native_run_rt import install, _uses_run, _run_entry


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
    def goto_target(self):
        return self.target
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

    def test_run_130_restarts_at_requested_original_line(self):
        obj = Module.Compiler(50)
        obj.reset([(1,b'\xf5\r'),(130,b'\xe3\r'),(8030,b'\xfa\xf7 130\r')])
        obj.layout_vars()
        obj.end = False
        obj.target = (False,130)
        obj.st_run()
        self.assertEqual(obj.calls[-1], ('goto','jp nn',130))
        self.assertIn(('rel','ld sp,(nn)',150),obj.calls)
        self.assertIn(('bc',49),obj.calls)

    def test_missing_run_target_uses_next_existing_line(self):
        obj = Module.Compiler()
        obj.reset([(1,b'\xf5\r'),(130,b'\xf7 129\r'),(200,b'\xf5\r')])
        obj.layout_vars()
        obj.end = False
        obj.target = (False,129)
        obj.st_run()
        self.assertEqual(obj.calls[-1],('goto','jp nn',130))

    def test_run_entry_bounds(self):
        lines = [(1,b''),(130,b''),(200,b'')]
        self.assertEqual(_run_entry(lines, 0),1)
        self.assertEqual(_run_entry(lines,129),130)
        for invalid in (-1, 0x4000, 9999, 1.5, None):
            self.assertIsNone(_run_entry(lines, invalid))

    def test_computed_run_target_rejected(self):
        obj = Module.Compiler(12)
        obj.reset([(1, b'\xf7 X\r')])
        obj.layout_vars()
        obj.end = False
        obj.target = (True,None)
        with self.assertRaisesRegex(ValueError, 'computed RUN line'):
            obj.st_run()

    def test_past_final_line_rejected(self):
        obj = Module.Compiler(12)
        obj.reset([(1, b'\xf7 9999\r')])
        obj.layout_vars()
        obj.end = False
        obj.target = (False,9999)
        with self.assertRaisesRegex(ValueError, 'RUN line outside listing'):
            obj.st_run()

    def test_original_evolution_1_run_reenters_same_listing(self):
        root = Path(__file__).resolve().parents[3]
        path = root / 'src/bonus/60-programs/44-evolution-1/BASIC/44-evolution-1.bas'
        numbered = {}
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            number, body = line.split(' ', 1)
            numbered[int(number)] = body.strip()
        self.assertIn(130, numbered)
        self.assertIn(8030, numbered)
        self.assertEqual(numbered[130], 'GO TO 1000')
        self.assertTrue(numbered[8030].endswith(':RUN 130'))
        self.assertEqual(_run_entry(sorted(numbered.items()),130),130)

    def test_install_is_repeatable(self):
        cls = Module.Compiler
        first = cls.st_run
        install(Module)
        self.assertIs(cls.st_run, first)
        self.assertIn(0xf7, cls().dispatch)

if __name__ == '__main__':
    unittest.main()

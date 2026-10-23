"""Check the repeated-FOR compiler fix without masking unrelated errors."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from for_restart import install


class TestRestart(unittest.TestCase):
    def _fixture(self):
        class Compiler:
            def __init__(self, state):
                self.fors = {0: {'flags': state, 'lim': 200, 'body': 300}}
                self.called = 0
            def get_char(self):
                return ord('x')
            def st_for(self):
                f = self.fors[0]
                if f['flags'] & 0x80:
                    raise RuntimeError('FOR inside FOR')
                self.called += 1
                f.update(flags=0x80, lim=400, body=500)
        class Module:
            pass
        Module.Compiler = Compiler
        Module.letter = lambda c: 0 if c in (ord('x'), ord('X')) else None
        return Module

    def test_restarted_for_owns_new_body(self):
        module = self._fixture()
        install(module)
        item = module.Compiler(0x80)
        item.st_for()
        self.assertEqual(item.called, 1)
        self.assertEqual(item.fors[0], {'flags': 0x80, 'lim': 400, 'body': 500})

    def test_restart_replaces_previous_step_flag(self):
        module = self._fixture()
        install(module)
        item = module.Compiler(0x81)
        item.st_for()
        self.assertEqual(item.fors[0]['flags'], 0x80)

    def test_normal_for_remains_normal(self):
        module = self._fixture()
        install(module)
        item = module.Compiler(0)
        item.st_for()
        self.assertEqual(item.called, 1)

    def test_install_is_idempotent(self):
        module = self._fixture()
        install(module)
        first = module.Compiler.st_for
        install(module)
        self.assertIs(module.Compiler.st_for, first)

    def test_unrelated_compiler_exception_propagates(self):
        module = self._fixture()
        def invalid(self):
            raise ValueError('bad expression')
        module.Compiler.st_for = invalid
        install(module)
        with self.assertRaisesRegex(ValueError, 'bad expression'):
            module.Compiler(0).st_for()


if __name__ == '__main__':
    unittest.main()
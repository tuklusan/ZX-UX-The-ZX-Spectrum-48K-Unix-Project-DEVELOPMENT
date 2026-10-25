"""The RBC setup script must remain executable and install the typed USR gate."""
import ast
import unittest
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1] / 'stage' / 'finish_rbc.py'


class FinishRbcSetup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = STAGE.read_text()
        cls.tree = ast.parse(cls.source, filename=str(STAGE))
        cls.changes = [node for node in ast.walk(cls.tree)
                       if isinstance(node, ast.Call)
                       and isinstance(node.func, ast.Name)
                       and node.func.id == 'change']

    def test_script_compiles(self):
        compile(self.source, str(STAGE), 'exec')

    def test_import_replacement_is_valid_python(self):
        imports = [node.args[1].value for node in self.changes
                   if len(node.args) == 2
                   and isinstance(node.args[0], ast.Constant)
                   and node.args[0].value == 'from bss_layout import target_offset']
        self.assertEqual(len(imports), 1)
        code = imports[0]
        self.assertIn('from safe_usr_rt import install as install_safe_usr\n', code)
        self.assertIn('from safety_usr import enforce_numeric_usr\n', code)
        self.assertEqual(code.count('from safe_usr_rt import'), 1)
        compile(code, '<RBC imports>', 'exec')

    def test_native_usr_install_is_present(self):
        entries = [node.args[1].value for node in self.changes
                   if len(node.args) == 2
                   and isinstance(node.args[0], ast.Constant)
                   and node.args[0].value == '    install_native_run(compiler)']
        self.assertEqual(entries, ['    install_native_run(compiler)\n'
                                   '    install_safe_usr(compiler)'])


if __name__ == '__main__':
    unittest.main()

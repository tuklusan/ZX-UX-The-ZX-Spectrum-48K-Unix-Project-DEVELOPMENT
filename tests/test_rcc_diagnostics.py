"""Diagnostic formatting does not change C48 acceptance, generated code or modes."""
import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
from rcc import driver
from rcc.diagnostics import classify, CATALOG, emit_tool_error
from rcc.lex import CError, Where, lex
import rld


class RCCDiagnostics(unittest.TestCase):
    def invoke(self, text, flags=('-S',)):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d)/'probe.c'
            source.write_text(text, encoding='ascii')
            target = Path(d)/('out.s' if '-S' in flags else 'out.ssx')
            out = io.StringIO()
            with contextlib.redirect_stderr(out):
                result = driver.main([str(source), '-o', str(target), *flags])
            contents = target.read_bytes() if target.exists() else None
            return result, out.getvalue(), contents

    def test_representative_diagnostic_families(self):
        cases = (
            ('int verylongcountername;\n', 'LEX_IDENTIFIER_LENGTH'),
            ('int main(void){ return 09; }\n', 'LEX_NUMBER_MALFORMED'),
            ('int main(void){ return "abc; }\n', 'LEX_LITERAL_UNTERMINATED'),
            ('#include <stdio.h>\n', 'PP_SYSTEM_HEADER'),
            ('#include "nonexistent-xyz.h"\n', 'PP_INCLUDE_MISSING'),
            ('#define VAL(X) 1\n', 'UNS_FUNCTION_MACRO'),
            ('int main(void) { return foobar; }\n', 'SEM_UNDECLARED'),
            ('int main(void) { int a[0]; return 0; }\n', 'SEM_ARRAY_BOUND_POSITIVE'),
            ('int main(void) { int a = 0; a += 1; return a; }\n', 'UNS_OPERATOR'),
            ('int main(void) { return; }\n', 'SEM_RETURN_VALUE_MISSING'),
            ('int main(void) { switch (1) { } return 0; }\n', 'UNS_RESERVED_KEYWORD'),
        )
        for source, mnemonic in cases:
            with self.subTest(mnemonic=mnemonic):
                status, stderr, data = self.invoke(source)
                self.assertEqual(status, 1, stderr)
                self.assertIsNone(data)
                self.assertIn('%RCC ' + mnemonic + ' Line: 1 Statement: -', stderr)
                if mnemonic == 'SEM_UNDECLARED':
                    self.assertIn("Identifier 'foobar' has not been declared.", stderr)
                self.assertIn('-RCC ' + source.strip(), stderr)
                self.assertIn('^', stderr)
                self.assertNotIn('Traceback', stderr)

    def test_precise_repeated_identifier_column(self):
        source = 'int main(void) { return z + z; }\n'
        status, stderr, _ = self.invoke(source)
        self.assertEqual(status, 1)
        pointer = stderr.splitlines()[-1]
        self.assertEqual(pointer.index('^') - len('-RCC '), source.index('z'))

    def test_tabs_align_caret(self):
        source = '\tint main(void){ return x; }\n'
        status, stderr, _ = self.invoke(source)
        self.assertEqual(status, 1)
        rows = stderr.splitlines()
        self.assertEqual(rows[-1].index('^'), len(rows[-2][:rows[-2].index('x')].expandtabs(8)))

    def test_global_diagnostic_no_fabricated_location(self):
        status, stderr, data = self.invoke('int main(void){return 0;}\n', ('--no-fit', '--native', '--max', '1'))
        self.assertEqual(status, 1)
        self.assertIsNone(data)
        self.assertIn('%RCC FIT_MEMORY_LIMIT Line: - Statement: -', stderr)
        self.assertNotIn('-RCC ', stderr)

    def test_cli_error_preserves_exit_code(self):
        out = io.StringIO()
        with contextlib.redirect_stderr(out):
            status = driver.main(['--udgs', '33'])
        self.assertEqual(status, 2)
        self.assertIn('%RCC CLI_UDG_RANGE Line: - Statement: -', out.getvalue())

    def test_native_linked_ssx_unaffected(self):
        status, stderr, data = self.invoke('int main(void){return 0;}\n', ('--no-fit', '--native'))
        self.assertEqual(status, 0, stderr)
        self.assertTrue(data)
        self.assertIn('image', rld.parse_ssx(data))

    def test_lexer_location_is_still_two_tuple(self):
        where = lex('abc', 'a.c')[0].where
        self.assertEqual(where, ('a.c', 1))
        self.assertEqual(where.column, 1)

    def test_tool_diagnostic_mnemonics(self):
        out = io.StringIO()
        with contextlib.redirect_stderr(out):
            emit_tool_error('ASM', ValueError('unknown section'))
            emit_tool_error('LNK', ValueError('undefined: _draw'))
        text = out.getvalue()
        self.assertIn('%RCC ASM_SECTION Line: - Statement: -', text)
        self.assertIn('%RCC LNK_UNDEFINED_SYMBOL Line: - Statement: -', text)


if __name__ == '__main__':
    unittest.main()

"""Four-family RBC diagnostics preserve source identity and native reports."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from diagnostics import MESSAGES, from_exception, format_failure, RbcArgumentParser


class UnifiedDiagnostics(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.source = Path(self.tmp.name) / 'example.bas'
        self.source.write_text('10 FOR I=1TO10\n'
                               '20 PRINT "USR 200"\n'
                               '30 RANDOMIZE USR 32768\n'
                               '40 IF A THEN PRINT "HEY": PRINT 2\n'
                               '50 LOAD "PART2"\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_all_proposed_families_and_historical_rom_codes(self):
        for name in ('BAS_NO_LINE_NUMBER', 'BAS_BIN_RANGE', 'ROM_C_SYNTAX',
                     'ROM_R_TAPE', 'ROM_0_OK', 'HIS_UNSUPPORTED',
                     'HIS_EXEC_ADDRESS', 'RBC_MEMORY_LIMIT', 'RBC_TZX_FIDELITY',
                     'RBC_SSX_DIFFERENCE'):
            self.assertIn(name, MESSAGES)

    def test_rom_syntax_uses_original_text_and_report_code(self):
        raw = 'Line 10: Spectrum 48K ROM syntax error 0B near character 15'
        result = from_exception(ValueError(raw), self.source)
        self.assertEqual((result.mnemonic, result.basic_line, result.statement,
                          result.native_code), ('ROM_C_SYNTAX', 10, 1, '0B'))
        self.assertEqual(result.detail, raw)
        self.assertIn('-RBC 10 FOR I=1TO10', result.render())
        self.assertIn('^', result.render())

    def test_rom_multi_statement_does_not_guess_caret(self):
        result = from_exception(ValueError(
            'Line 40: Spectrum 48K ROM syntax error 0B near character 28'), self.source)
        self.assertEqual((result.basic_line, result.statement,
                          result.source_column), (40, None, None))
        self.assertIn('-RBC 40 IF A THEN', result.render())
        self.assertNotIn('^', result.render())

    def test_numeric_usr_is_distinct_from_inert_quoted_usr(self):
        raw = 'RBC E_USR_TOKEN: Line 30: USR requires a proved UDG POKE address'
        result = from_exception(ValueError(raw), self.source)
        self.assertEqual(result.mnemonic, 'RBC_USR_MACHINE_CODE')
        self.assertEqual(result.statement, 1)
        self.assertIn('RANDOMIZE USR 32768', result.render())

    def test_external_tape_error_has_keyword_caret(self):
        result = from_exception(ValueError(
            'RBC E_TAPE_UNSUPPORTED: Line 50: LOAD requires external tape I/O'),
            self.source)
        self.assertEqual(result.mnemonic, 'RBC_TAPE_LOAD')
        self.assertEqual(result.source_text, '50 LOAD "PART2"')
        self.assertEqual(result.source_column, 3)

    def test_hisoft_keeps_numeric_code_and_specific_reason(self):
        result = from_exception(ValueError(
            'example.bas: HiSoft v1.1 compile failed: 103 line 40: DIM again, with different sizes'),
            self.source)
        self.assertEqual(result.mnemonic, 'HIS_UNSUPPORTED')
        self.assertEqual(result.native_code, '103')
        self.assertIn('DIM again, with different sizes', result.message)

    def test_limit_exact_measured_bytes_and_no_fake_caret(self):
        report = format_failure(ValueError(
            'example.bas needs 12903 bytes of native memory (limit 11000)'), self.source)
        self.assertEqual(report,
            '%RBC RBC_MEMORY_LIMIT Line: - Statement: - Executable requires 12903 '
            'bytes of native memory; the configured compile limit is 11000 bytes.')

    def test_physical_line_does_not_become_basic_line(self):
        result = from_exception(ValueError('ASCII line 20: missing line number'),
                                self.source)
        self.assertIsNone(result.basic_line)
        self.assertIn('Physical ASCII file line 20.', result.message)

    def test_file_wide_io_failure_has_one_line(self):
        report = format_failure(OSError('example.bas: no such file'), None)
        self.assertEqual(report.count('\n'), 0)
        self.assertTrue(report.startswith('%RBC RBC_INPUT_READ Line: - Statement: -'))

    def test_invalid_cli_preserves_exit_status_two(self):
        parser = RbcArgumentParser(prog='rbc')
        parser.add_argument('--max', type=int)
        with self.assertRaises(SystemExit) as caught:
            parser.parse_args(['--max', 'INVALID'])
        self.assertEqual(caught.exception.code, 2)

if __name__ == '__main__':
    unittest.main()

"""Native 48K BASIC regression tests for functions, VAL and safe channels."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / 'src/zx-ux-sdk'
sys.path.insert(0, str(SDK))
import rld


class RomCompatibility(unittest.TestCase):
    def compile_case(self, listing, accepted=True):
        with tempfile.TemporaryDirectory(prefix='rbc-rom-') as folder:
            source = Path(folder) / 'example.bas'
            target = Path(folder) / 'example.ssx'
            source.write_text(listing, encoding='ascii')
            before = source.read_bytes()
            command = [sys.executable, '-B', str(SDK / 'bin/rbc'),
                       str(source), '-o', str(target)]
            completed = subprocess.run(command, cwd=ROOT, text=True,
                                       capture_output=True, timeout=150)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(completed.returncode == 0, accepted,
                             completed.stderr + completed.stdout)
            if accepted:
                self.assertTrue(target.is_file())
                rld.parse_ssx(target.read_bytes())
                return target.read_bytes()
            self.assertFalse(target.exists())
            return completed.stderr

    def test_fn_zero_arguments(self):
        self.compile_case('10 DEF FN a()=5\n20 PRINT FN a()\n')

    def test_fn_five_mixed_arguments(self):
        self.compile_case(
            '10 DEF FN f(a,b$,c,d$,e)=a+c+e+LEN b$+LEN d$\n'
            '20 PRINT FN f(1,"AB",2,"CD",3)\n')

    def test_fn_string_result(self):
        self.compile_case(
            '10 DEF FN g$(a$,b,c$)=a$+STR$ b+c$\n'
            '20 PRINT FN g$("X",7,"Y")\n')

    def test_fn_parameter_type_mismatch(self):
        self.compile_case(
            '10 DEF FN f(a$,b)=LEN a$+b\n'
            '20 PRINT FN f(5,6)\n', accepted=False)

    def test_fn_parameter_count_mismatch(self):
        self.compile_case(
            '10 DEF FN f(a,b,c,d,e)=a+b+c+d+e\n'
            '20 PRINT FN f(1,2,3,4)\n', accepted=False)

    def test_val_runtime_string(self):
        self.compile_case('10 LET a$="12+3"\n20 PRINT VAL a$\n')

    def test_vals_runtime_string(self):
        self.compile_case('10 LET a$=CHR$ 34+"12"+CHR$ 34\n20 PRINT VAL$ a$\n')

    def test_screen_and_keyboard_literal_channels(self):
        self.compile_case('10 OPEN #4,"S"\n20 PRINT #4;"SCREEN"\n30 CLOSE #4\n')
        self.compile_case('10 PRINT #0;"LOWER SCREEN"\n')
        self.compile_case('10 OPEN #5,"K"\n20 CLOSE #5\n')

    def test_unsafe_channels_refused(self):
        for source in (
            '10 OPEN #4,"P"\n',
            '10 OPEN #a,"S"\n',
            '10 CLOSE #a\n',
            '10 PRINT #3;"PRINTER"\n',
            '10 PRINT #a;"UNKNOWN"\n',
            '10 OPEN #3,"S"\n',
            '10 PRINT #4;"NOT OPEN"\n',
            '10 PRINT #4;"BEFORE"\n20 OPEN #4,"S"\n',
            '10 CLOSE #4\n',
            '10 OPEN #4,"S"\n20 CLOSE #4\n30 PRINT #4;"AFTER"\n',
            '10 CLOSE #0\n20 PRINT #0;"CLOSED"\n',
        ):
            with self.subTest(source=source):
                self.compile_case(source, accepted=False)

    def test_editor_and_printer_commands_refused(self):
        for source in ('10 COPY\n', '10 NEW\n', '10 LIST\n',
                       '10 LLIST\n', '10 LPRINT "NO"\n'):
            with self.subTest(source=source):
                self.compile_case(source, accepted=False)


    def test_fn_zero_arguments_string_result(self):
        self.compile_case(
            '10 DEF FN g$()="READY"\n20 PRINT FN g$()\n')

    def test_fn_six_mixed_arguments(self):
        self.compile_case(
            '10 DEF FN f(a,b$,c,d$,e,f$)=a+c+e+LEN b$+LEN d$+LEN f$\n'
            '20 PRINT FN f(1,"A",2,"B",3,"C")\n')

    def test_native_fn_val_vals_and_screen_streams(self):
        sys.path.insert(0, str(ROOT / 'dist/sdk/bin/py'))
        import rvm

        listing = (
            '10 DEF FN a()=5\n'
            '20 DEF FN f(a,b$,c,d$,e)=a+c+e+LEN b$+LEN d$\n'
            '30 DEF FN g$(a$,b,c$)=a$+STR$ b+c$\n'
            '40 LET a$="12+3"\n'
            '50 LET b$=CHR$ 34+"12"+CHR$ 34\n'
            '60 OPEN #4,"S"\n'
            '70 PRINT #4;"FN0=";FN a()\n'
            '80 PRINT #4;"FN5=";FN f(1,"AB",2,"CD",3)\n'
            '90 PRINT #4;"FNS=";FN g$("X",7,"Y")\n'
            '100 PRINT #4;"VAL=";VAL a$\n'
            '110 PRINT #4;"VALS=";VAL$ b$\n'
            '115 PRINT #0;"LOWER"\n'
            '120 CLOSE #4\n'
            '130 GO TO 130\n'
        )
        expected = ('FN0=5', 'FN5=10', 'FNS=X7Y', 'VAL=15', 'VALS=12', 'LOWER')
        font = (SDK / 'rbc/font32.bin').read_bytes()
        glyphs = {font[n:n + 8]: chr(n // 8 + 32)
                  for n in range(0, 768, 8)}
        with tempfile.TemporaryDirectory(prefix='rbc-native-rom-') as folder:
            source = Path(folder) / 'probe.bas'
            target = Path(folder) / 'probe.ssx'
            source.write_text(listing, encoding='ascii')
            original = source.read_bytes()
            result = subprocess.run(
                [sys.executable, '-B', str(SDK / 'bin/rbc'),
                 str(source), '-o', str(target)],
                cwd=ROOT, capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0,
                             result.stderr + result.stdout)
            self.assertEqual(source.read_bytes(), original)
            rld.parse_ssx(target.read_bytes())
            opts = rvm.Options()
            opts.prog = str(target)
            opts.system = str(ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx')
            opts.headless = True
            runner = rvm.Runner(opts)
            runner.start()
            last = ''
            reason = None
            for frame in range(4500):
                runner.frame()
                job = runner.fg
                if job is not None and job.started is not None:
                    owned = runner.session.program_screen(job)
                    image = owned[0] if owned is not None else runner.session.m.screen()
                    if len(image) == 6912:
                        rows = []
                        for row in range(24):
                            chars = []
                            for col in range(32):
                                at = ((row & 24) << 8) + ((row & 7) << 5) + col
                                shape = bytes(image[at + (y << 8)]
                                              for y in range(8))
                                chars.append(glyphs.get(shape, '#'))
                            rows.append(''.join(chars))
                        last = '\n'.join(rows)
                        if all(phrase in last for phrase in expected):
                            return
                reason = runner.check(limit=4000)
                if reason:
                    break
            self.fail('Native ROM screen did not match expected output: '
                      + str(reason) + ' ' + repr(last)[-1000:])



    def test_dynamic_val_rejects_unchecked_peek_at_runtime(self):
        sys.path.insert(0, str(ROOT / 'dist/sdk/bin/py'))
        import rvm

        listing = '10 LET a$=CHR$ 190+" 0"\n20 PRINT VAL a$\n30 GO TO 30\n'
        with tempfile.TemporaryDirectory(prefix='rbc-peek-guard-') as folder:
            source = Path(folder) / 'probe.bas'
            output = Path(folder) / 'probe.ssx'
            source.write_text(listing, encoding='ascii')
            original = source.read_bytes()
            result = subprocess.run(
                [sys.executable, '-B', str(SDK / 'bin/rbc'),
                 str(source), '-o', str(output)],
                cwd=ROOT, capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0,
                             result.stderr + result.stdout)
            self.assertEqual(source.read_bytes(), original)
            rld.parse_ssx(output.read_bytes())
            opts = rvm.Options()
            opts.prog = str(output)
            opts.system = str(ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx')
            opts.headless = True
            runner = rvm.Runner(opts)
            runner.start()
            reason = None
            for _ in range(2500):
                runner.frame()
                reason = runner.check(limit=2200)
                if reason is not None:
                    break
            self.assertEqual(reason, 'exit',
                             'unchecked PEEK did not exit through native guard')
            self.assertIsNotNone(runner.fg)
            self.assertNotEqual(runner.fg.status, 0)



if __name__ == '__main__':
    unittest.main()

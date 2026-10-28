"""Actual 48K ROM and HiSoft v1.1 checks for constant DATA arithmetic."""
from __future__ import annotations
import os
import sys
from pathlib import Path
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from native_data_expressions import with_literal_data_expressions


class InstallerTests(unittest.TestCase):
    def test_other_number_paths_are_unchanged(self):
        class Base:
            def number_maybe_val(self):
                self.called = True
        c = with_literal_data_expressions(Base)()
        c.number_maybe_val()
        self.assertTrue(c.called)

    def test_data_flag_clears_after_error(self):
        class Base:
            def st_data(self):
                raise ValueError('intentional fault')
        c = with_literal_data_expressions(Base)()
        with self.assertRaisesRegex(ValueError, 'intentional fault'):
            c.st_data()
        self.assertFalse(c._zxux_in_data)


FRONTEND = Path(os.environ.get('RBC_TEST_FRONTEND', '')) if os.environ.get('RBC_TEST_FRONTEND') else None
TAPE = Path(os.environ.get('RBC_TEST_HISOFT_TAPE', '')) if os.environ.get('RBC_TEST_HISOFT_TAPE') else None
ROM = Path(os.environ.get('RBC_TEST_ROM', '')) if os.environ.get('RBC_TEST_ROM') else None
READY = bool(FRONTEND and FRONTEND.is_file() is False and (FRONTEND / 'compiler.py').is_file()
             and TAPE and TAPE.is_file() and ROM and ROM.is_file())
if READY:
    sys.path.insert(0, str(FRONTEND))
    import compiler, hbcimage, source
    from basic_listing import encode_strict_listing


@unittest.skipUnless(READY, 'set RBC_TEST_FRONTEND, RBC_TEST_HISOFT_TAPE and RBC_TEST_ROM')
class OriginalRomNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()
        cls.img = hbcimage.Image.from_tape(TAPE)
        assert cls.img.v11
        cls.kw = source.Keywords(cls.rom)
        cls.typ = with_literal_data_expressions(compiler.Compiler)

    def compile_listing(self, listing, typ=None):
        c = (typ or self.typ)(self.img, self.rom)
        prog = encode_strict_listing(listing)
        prog = source.add_directives(prog, [], True, [], self.kw, c.fp)
        prog = source.tokenize_directives(prog, self.kw)
        res = c.compile_whole(prog)
        return c, res

    def test_precedence_parentheses_and_sign(self):
        c, res = self.compile_listing('10 DATA 2+3*4,(2+3)*4,5/2,7-10\n20 READ A,B,C,D\n30 PRINT A,B,C,D\n')
        self.assertTrue(res.ok, (res.error, res.detail))
        values = [bytes(c.far[c.data_start+i*5:c.data_start+(i+1)*5]) for i in range(4)]
        self.assertEqual([c.fp.round_to_hl(n) for n in values], [14, 20, 3, 65533])

    def test_fractions_use_real_rom_calculator(self):
        c, res = self.compile_listing('10 DATA .1+.2,1/3\n20 READ A,B\n')
        self.assertTrue(res.ok, (res.error, res.detail))
        import re
        numbers = re.findall(rb'\x0e(.{5})', encode_strict_listing('10 DATA .1+.2,1/3\n'), re.S)
        self.assertEqual(len(numbers), 4)
        n, m = numbers[:2]
        wanted = c.fp.calc([n, m], [0x0F])[-1]
        self.assertEqual(bytes(c.far[c.data_start:c.data_start+5]), wanted)

    def test_power_precedence_and_rom_exact_result(self):
        from romfp import int_form
        c, res = self.compile_listing(
            '10 DATA 2^3^2,-2^2,(2+1)^2,2^-2\n'
            '20 READ A,B,C,D\n')
        self.assertTrue(res.ok, (res.error, res.detail))
        values = [bytes(c.far[c.data_start + i * 5:
                              c.data_start + (i + 1) * 5]) for i in range(4)]
        # Keep the ROM's intermediate FP rounding; 3^2 is not necessarily
        # byte-identical to the 5-byte integer literal 9.
        rhs = c.fp.calc([int_form(3), int_form(2)], [0x06])[-1]
        self.assertEqual(values[0],
                         c.fp.calc([int_form(2), rhs], [0x06])[-1])
        self.assertEqual(values[1],
                         c.fp.negate(c.fp.calc([int_form(2), int_form(2)], [0x06])[-1]))
        self.assertEqual(values[2],
                         c.fp.calc([int_form(3), int_form(2)], [0x06])[-1])
        self.assertEqual(values[3],
                         c.fp.calc([int_form(2), int_form(-2)], [0x06])[-1])

    def test_rom_pi_in_numeric_data_expressions(self):
        from romfp import int_form
        c, res = self.compile_listing(
            '10 DATA PI,2*PI,PI/2\n20 READ A,B,C\n')
        self.assertTrue(res.ok, (res.error, res.detail))
        values = [bytes(c.far[c.data_start + 5*i:c.data_start + 5*(i+1)])
                  for i in range(3)]
        pi = c.fp.calc([], [0xA3, 0xA1, 0x04])[-1]
        self.assertEqual(values, [
            pi,
            c.fp.calc([int_form(2), pi], [0x04])[-1],
            c.fp.calc([pi, int_form(2)], [0x05])[-1],
        ])

    def test_dynamic_scalar_data_uses_native_relocatable_live_real_reference(self):
        from romfp import int_form
        c, res = self.compile_listing(
            '10 LET F=5: LET G=7\n'
            '20 RESTORE 80: READ A,B,C\n'
            '80 DATA F,2*PI,G\n')
        self.assertTrue(res.ok, (res.error, res.detail))
        addresses = {name: addr for name, typ, addr in res.variables}
        data = bytes(c.far[c.data_start:c.vars_start])
        for index, name in ((0, 'f'), (2, 'g')):
            address = addresses[name]
            self.assertEqual(data[index*5:index*5+5],
                             bytes((0, 0x7e, address & 255, address >> 8, 0)))
        pi = c.fp.calc([], [0xA3, 0xA1, 0x04])[-1]
        self.assertEqual(data[5:10], c.fp.calc([int_form(2), pi], [0x04])[-1])

    def test_rom_executes_dynamic_numeric_read_at_live_variable_value(self):
        from z80asm import asm
        from z80_python.cpu import Z80CPU
        from native_data_expressions import _READ_DYNAMIC_BODY
        c, res = self.compile_listing(
            '10 LET F=5\n20 RESTORE 80: READ A\n80 DATA F\n')
        self.assertTrue(res.ok, (res.error, res.detail))
        from compiler import ROM as ROM_ADDRESSES, RT
        rt_read = dict(res.rts)[RT.READ_REAL]
        body = asm(_READ_DYNAMIC_BODY.format(ROM_ADDRESSES['STACK_NUM']))
        prefix = asm('ld hl,($5C6C); ld a,(hl); or a; '
                     'jr nz,+{}; inc hl; ld a,(hl); cp $7e; jr nz,+{}'.format(
                         len(body) + 6, len(body)))
        real_read = asm('call {} ; ret'.format(rt_read))
        guarded_read = prefix + body + real_read
        self.assertIn(guarded_read[:-1], res.code)
        variable = next(addr for name, kind, addr in res.variables if name == 'f')
        field = res.load + c.data_start
        def execute(number, *, fallback=False, guarded=True):
            memory = bytearray(65536)
            memory[:0x4000] = self.rom
            memory[res.load:res.load+len(res.code)] = res.code
            memory[0x8000:0x8000+len(guarded_read)] = guarded_read
            memory[0x8200:0x8200+len(real_read)] = real_read
            fp = bytes((0, 0, number, 0, 0))
            memory[variable:variable + 5] = fp
            if fallback:
                memory[field:field+5] = fp
            memory[0x5C6C:0x5C6E] = field.to_bytes(2, 'little')
            memory[0x5C65:0x5C67] = (0x9000).to_bytes(2, 'little')
            memory[0x5C63:0x5C65] = (0x9000).to_bytes(2, 'little')
            memory[0xA000:0xA002] = (0xF000).to_bytes(2, 'little')
            cpu = Z80CPU(lambda a: memory[a],
                         lambda a, v: memory.__setitem__(a, v))
            cpu.pc = 0x8000 if guarded else 0x8200
            cpu.sp = 0xA000
            cpu.iy = 0x5C3A
            for _ in range(500):
                if cpu.pc == 0xF000:
                    break
                cpu.step()
            self.assertEqual(cpu.pc, 0xF000)
            self.assertEqual(cpu.sp, 0xA002)
            self.assertEqual(memory[0x5C6C:0x5C6E], (field+5).to_bytes(2,'little'))
            self.assertEqual(memory[0x5C65:0x5C67], (0x9005).to_bytes(2,'little'))
            return memory[0x9000:0x9005]
        for value in (5, 7, 11, 63):
            with self.subTest(value=value):
                self.assertEqual(execute(value), execute(value, fallback=True,
                                                         guarded=False))
                self.assertEqual(execute(value, fallback=True),
                                 execute(value, fallback=True, guarded=False))

    def test_linked_native_data_reference_relocates_into_bss(self):
        import subprocess
        import tempfile
        from z80asm import asm
        from z80_python.cpu import Z80CPU
        from native_data_expressions import _READ_DYNAMIC_BODY
        import rld
        checkpoint = Path(os.environ.get('RBC_G8_CHECKPOINT', ''))
        if not (checkpoint / 'rbc.py').is_file():
            self.skipTest('set RBC_G8_CHECKPOINT to recovered RBC compiler')
        with tempfile.TemporaryDirectory() as folder:
            bas = Path(folder) / 'live-data.bas'
            ssx = Path(folder) / 'live-data.ssx'
            bas.write_text('10 LET F=5: RESTORE 100: READ A\n'
                           '20 LET F=11: RESTORE 100: READ B\n'
                           '100 DATA F\n', encoding='ascii')
            proc = subprocess.run([
                sys.executable, str(checkpoint / 'rbc.py'), str(bas),
                '--frontend', str(FRONTEND), '--tape', str(TAPE),
                '--rom', str(ROM), '--sdk', str(STAGE.parents[2] / 'src/zx-ux-sdk'),
                '-o', str(ssx)], capture_output=True, text=True,
                timeout=120)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            parsed = rld.parse_ssx(ssx.read_bytes())
            image = parsed['image']
            locations = [(i, int.from_bytes(image[i+2:i+4], 'little'))
                         for i in range(len(image)-4)
                         if image[i:i+2] == b'\x00\x7e'
                         and i+2 in parsed['relocs']
                         and len(image) <= int.from_bytes(image[i+2:i+4], 'little')
                         < len(image) + parsed['bss']]
            self.assertEqual(len(locations), 1, locations)
            site, target = locations[0]
            self.assertEqual(target, len(image))  # the live F variable
            from compiler import ROM as ROM_ADDRESSES
            body = asm(_READ_DYNAMIC_BODY.format(ROM_ADDRESSES['STACK_NUM']))
            prefix = asm('ld hl,($5C6C); ld a,(hl); or a; '
                         'jr nz,+{}; inc hl; ld a,(hl); cp $7e; jr nz,+{}'.format(
                             len(body) + 6, len(body)))
            # The synthetic return executes only after the descriptor path.
            # An ordinary READ would branch to the deliberately invalid CALL.
            probe = prefix + body + b'\xcd\x00\x00\xc9'
            for base in (0x6000, 0x7000, 0x8000):
                with self.subTest(base=base):
                    memory = bytearray(65536)
                    memory[:0x4000] = self.rom
                    memory[base:base+len(image)] = rld.relocate(
                        image, parsed['relocs'], base)
                    address = int.from_bytes(memory[base+site+2:base+site+4], 'little')
                    self.assertEqual(address, base + len(image))
                    memory[address:address+5] = bytes((0, 0, 11, 0, 0))
                    memory[0x5C6C:0x5C6E] = (base+site).to_bytes(2, 'little')
                    memory[0x5C65:0x5C67] = (0x9000).to_bytes(2, 'little')
                    memory[0x5C63:0x5C65] = (0x9000).to_bytes(2, 'little')
                    memory[0xA000:0xA000+len(probe)] = probe
                    memory[0xB000:0xB002] = (0xF000).to_bytes(2, 'little')
                    cpu = Z80CPU(lambda a: memory[a],
                                 lambda a, v: memory.__setitem__(a, v))
                    cpu.pc, cpu.sp, cpu.iy = 0xA000, 0xB000, 0x5C3A
                    for _ in range(500):
                        if cpu.pc == 0xF000:
                            break
                        cpu.step()
                    self.assertEqual(cpu.pc, 0xF000)
                    self.assertEqual(memory[0x9000:0x9005],
                                     bytes((0, 0, 11, 0, 0)))
                    self.assertEqual(memory[0x5C6C:0x5C6E],
                                     (base+site+5).to_bytes(2, 'little'))

    def test_original_boxing_both_sources_same_native_audit(self):
        import importlib
        import json
        import subprocess
        import tempfile
        import rld
        from dual_source import convert_tzx
        checkpoint = Path(os.environ.get('RBC_G8_CHECKPOINT', ''))
        if not (checkpoint / 'rbc.py').is_file():
            self.skipTest('set RBC_G8_CHECKPOINT to recovered RBC compiler')
        sys.path.insert(0, str(checkpoint))
        rbc = importlib.import_module('rbc')
        root = STAGE.parents[2]
        folder = root / 'src/bonus/60-programs/05-championship-boxing/BASIC'
        bas = folder / '05-championship-boxing.bas'
        tzx = folder / '05-championship-boxing.tzx'
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            ascii_tzx = temp / 'from-tzx.bas'
            converted = convert_tzx(tzx, bas, ascii_tzx, rbc, source,
                                    self.kw, self.typ(self.img, self.rom).fp)
            self.assertEqual(converted['source_lines'], 130)
            outputs = []
            for input_file in (bas, ascii_tzx):
                destination = temp / (input_file.stem + '.ssx')
                report = destination.with_suffix('.json')
                # Trial only: do not relax RBC's normal 14 KB admission.
                cmd = [sys.executable, str(checkpoint / 'rbc.py'),
                       str(input_file), '--frontend', str(FRONTEND),
                       '--tape', str(TAPE), '--rom', str(ROM),
                       '--sdk', str(root / 'src/zx-ux-sdk'),
                       '--max', '20000', '-o', str(destination),
                       '--report', str(report)]
                env = dict(os.environ)
                env['PYTHONPATH'] = os.pathsep.join(
                    (str(checkpoint), str(FRONTEND), str(STAGE),
                     str(root / 'src/zx-ux-sdk'), env.get('PYTHONPATH', '')))
                result = subprocess.run(cmd, capture_output=True, text=True,
                                        timeout=120, env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(report.read_text())['memory_limit'],
                                 20000)
                outputs.append(destination.read_bytes())
            self.assertEqual(outputs[0], outputs[1])
            parsed = rld.parse_ssx(outputs[0])
            image = parsed['image']
            refs = [(i, int.from_bytes(image[i+2:i+4], 'little'))
                    for i in range(len(image)-4)
                    if image[i:i+2] == b'\x00\x7e'
                    and i+2 in parsed['relocs']]
            self.assertTrue(refs)
            for site, variable in refs:
                self.assertLessEqual(len(image), variable)
                self.assertLess(variable, len(image) + parsed['bss'])

    def test_dynamic_data_string_reads_guard_wrong_type(self):
        from z80asm import asm
        c, res = self.compile_listing(
            '10 DATA "hello",F\n20 READ A$,B\n')
        self.assertTrue(res.ok, (res.error, res.detail))
        self.assertIn(asm('ld hl,($5C6C); ld a,(hl); or a; jr nz,+8; '
                          'inc hl; ld a,(hl); cp 126; jr nz,+2; '
                          'rst 8; defb $0B'), res.code)

    def test_dynamic_data_complex_expressions_still_rejected(self):
        for expr in ('F+1', 'F^2', 'F(1)', 'INT F', 'SQR F'):
            with self.subTest(expr=expr):
                _, res = self.compile_listing('10 DATA '+expr+'\n20 READ X\n')
                self.assertFalse(res.ok)

    def test_plain_literals_produce_identical_code(self):
        listing = '10 DATA 1,-2,.25,5\n20 READ A,B,C,D\n30 PRINT A,B,C,D\n'
        _, old = self.compile_listing(listing, compiler.Compiler)
        _, new = self.compile_listing(listing)
        self.assertTrue(old.ok)
        self.assertTrue(new.ok)
        self.assertEqual(old.code, new.code)
        self.assertEqual(old.var_bytes, new.var_bytes)

    def test_strings_not_evaluated(self):
        c, res = self.compile_listing('10 DATA "2+3",1+2\n20 READ A$,A\n')
        self.assertTrue(res.ok, (res.error, res.detail))
        self.assertIn(b'2+3', res.code)

    def test_value_dependent_data_fails_closed(self):
        for data in ['A+1', 'RND+1', 'INT (5/2)', 'A^2', '(-2)^2']:
            with self.subTest(data=data):
                _, res = self.compile_listing('10 DATA '+data+'\n20 READ A\n')
                self.assertFalse(res.ok)


if __name__ == '__main__':
    unittest.main()

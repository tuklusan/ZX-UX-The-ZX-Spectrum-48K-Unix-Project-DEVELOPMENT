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
        for data in ['A+1', 'RND+1', 'INT (5/2)', '2^3']:
            with self.subTest(data=data):
                _, res = self.compile_listing('10 DATA '+data+'\n20 READ A\n')
                self.assertFalse(res.ok)


if __name__ == '__main__':
    unittest.main()

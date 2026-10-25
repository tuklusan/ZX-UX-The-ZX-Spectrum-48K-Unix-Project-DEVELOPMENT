"""Bounded typed native DIM: scalar proof, ROM compile, Z80 memory guards."""
import os
import sys
from pathlib import Path
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from native_dynamic_dim import _proved_dimensions, with_bounded_dynamic_dims

FRONTEND = Path(os.environ['RBC_TEST_FRONTEND']) if 'RBC_TEST_FRONTEND' in os.environ else None
TAPE = Path(os.environ['RBC_TEST_HISOFT_TAPE']) if 'RBC_TEST_HISOFT_TAPE' in os.environ else None
ROM = Path(os.environ['RBC_TEST_ROM']) if 'RBC_TEST_ROM' in os.environ else None
READY = bool(FRONTEND and (FRONTEND / 'compiler.py').is_file()
             and TAPE and TAPE.is_file() and ROM and ROM.is_file())
if READY:
    sys.path.insert(0, str(FRONTEND))
    import compiler, hbcimage, source, tap
    from basic_listing import encode_strict_listing
    from z80asm import asm
    from z80mini import Z80


@unittest.skipUnless(READY, 'needs HiSoft frontend, 48K tape and 48K ROM')
class BoundedDynamicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()
        cls.img = hbcimage.Image.from_tape(TAPE)
        assert cls.img.v11
        cls.kw = source.Keywords(cls.rom)
        cls.backend = with_bounded_dynamic_dims(
            compiler.Compiler, real_type=compiler.REAL,
            memfill_rt=compiler.RT.MEM_FILL)

    def program(self, listing):
        c = compiler.Compiler(self.img, self.rom)
        program = encode_strict_listing(listing)
        program = source.add_directives(program, [], True, [], self.kw, c.fp)
        return source.tokenize_directives(program, self.kw)

    def plan(self, listing):
        return _proved_dimensions(tap.split_lines(self.program(listing)))

    def test_multiple_runtime_shapes_without_rewriting_basic(self):
        code = ('10 LET N=3: DIM A(N)\n'
                '20 FOR I=1 TO N: LET A(I)=I*2: NEXT I\n'
                '30 LET N=5: DIM A(N)\n'
                '40 LET A(5)=99: PRINT A(5)\n')
        original = self.program(code)
        self.assertEqual(self.plan(code), {0: (b'n', 5)})
        new = self.backend(self.img, self.rom)
        compiled = new.compile_whole(original)
        self.assertTrue(compiled.ok, (compiled.error, compiled.detail))
        self.assertEqual(new._zxux_dynamic_dims[0][1], 5)
        self.assertEqual(new.arrays[0]['last'], 5)
        self.assertEqual(new.arrays[0]['zxux_dynamic_slot'], new.arrays[0]['addr']+25)
        self.assertEqual(original, self.program(code))
        old = compiler.Compiler(self.img, self.rom).compile_whole(original)
        self.assertFalse(old.ok)

    def test_only_literal_scalar_writes_count(self):
        cases = [
            '10 INPUT N: DIM A(N)\n20 PRINT A(1)\n',
            '10 LET N=N+1: DIM A(N)\n',
            '10 LET N=3: FOR N=1 TO 10: NEXT N: DIM A(N)\n',
            '10 LET N=3: READ N: DIM A(N)\n20 DATA 4\n',
            '10 LET N=3: DIM A(N): DIM A(4)\n',
            '10 LET N=3: LET N=0: DIM A(N)\n',
        ]
        for listing in cases:
            with self.subTest(listing=listing):
                self.assertEqual(self.plan(listing), {})

    def test_strings_and_comments_do_not_declare_arrays(self):
        listing = ('10 PRINT "DIM A(N)": REM DIM B(N)\n'
                   '20 DATA "DIM C(N)"\n'
                   '30 LET N=5: DIM D(N)\n')
        self.assertEqual(self.plan(listing), {3: (b'n', 5)})

    def test_unproved_case_fails_closed(self):
        c = self.backend(self.img, self.rom)
        result = c.compile_whole(self.program('10 INPUT N: DIM A(N)\n20 PRINT A(1)\n'))
        self.assertFalse(result.ok)

    def test_proved_runtime_arithmetic_and_long_scalar_names(self):
        fixtures = [
            ('10 LET N=2: LET K=3: DIM A(N+K)\n20 LET A(4)=9\n', 5),
            ('10 LET N=7: DIM A(N-2)\n20 PRINT A(5)\n', 5),
            ('10 LET LB=5: DIM A(LB)\n20 PRINT A(4)\n', 5),
            ('10 LET LB=5: LET KC=2: DIM A(LB+KC)\n20 PRINT A(6)\n', 7),
            ('10 LET N=7: LET K=3: DIM A(N-K)\n20 PRINT A(4)\n', 4),
            ('10 LET N=3: LET N=8: DIM A(N+2)\n20 PRINT A(5)\n', 10),
            ('10 LET N=3: LET N=8: DIM A(N+N)\n20 PRINT A(5)\n', 16),
        ]
        for listing, capacity in fixtures:
            with self.subTest(listing=listing):
                original = self.program(listing)
                proof = self.plan(listing)
                self.assertEqual(proof[0][1], capacity)
                c = self.backend(self.img, self.rom)
                result = c.compile_whole(original)
                self.assertTrue(result.ok, (listing, result.error, result.detail))
                self.assertEqual(c.arrays[0]['last'], capacity)
                self.assertEqual(self.program(listing), original)

    def test_arithmetic_bounds_and_multiletter_inputs_fail_closed(self):
        invalid = [
            '10 LET N=5: LET K=6: DIM A(N-K)\n',
            '10 LET N=8000: LET K=6000: DIM A(N+K)\n',
            '10 LET N=5: LET K=2: READ K: DIM A(N+K)\n20 DATA 2\n',
            '10 LET LB=5: INPUT LB: DIM A(LB)\n',
            '10 LET LB=5: FOR LB=1 TO 10: NEXT LB: DIM A(LB)\n',
            '10 LET LB=5: LET LB=VAL "2": DIM A(LB)\n',
            '10 LET LB=5: DIM A(LB): DIM A(LB,2)\n',
            '10 LET LB=5: DIM A(LB*2)\n',
            '10 LET N=3: DIM A(N+K)\n',
            '10 LET N=3: DIM A(N+20000)\n',
        ]
        for listing in invalid:
            with self.subTest(listing=listing):
                self.assertEqual(self.plan(listing), {})

    def test_nonexecuted_prose_cannot_supply_arithmetic_proofs(self):
        listing = ('10 PRINT "LET K=5: DIM A(N+K)"\n'
                   '20 REM LET K=5: DIM A(N+K)\n'
                   '30 DATA "LET K=5", 2\n'
                   '40 LET N=4: DIM A(N+K)\n')
        self.assertEqual(self.plan(listing), {})

    def guards(self, kind, bound):
        chunks = []
        class Stub:
            def emit(self, text, *args):
                chunks.extend(asm(text, *args))
            def ld_hl_ind(self, slot):
                chunks.extend(asm('ld hl,({})', slot))
        obj = with_bounded_dynamic_dims(Stub, real_type=0, memfill_rt=0)()
        if kind == 'count':
            obj._zxux_valid_count(bound)
        else:
            obj._zxux_valid_index(bound)
        return bytes(chunks) + b'\xc9'

    def run_guard(self, kind, bound, value, live=3):
        mem = bytearray(65536)
        code = self.guards(kind, bound)
        mem[0x7100:0x7100+len(code)] = code
        mem[0x8000:0x8002] = live.to_bytes(2,'little')
        cpu = Z80(mem)
        cpu.hl = value
        cpu.sp = 0x9000
        cpu.hooks[8] = lambda _: (_ for _ in ()).throw(IndexError('ROM subscript error'))
        cpu.call(0x7100)
        self.assertEqual(cpu.hl, value)

    def test_zero_and_overflow_raise_before_index_arithmetic(self):
        for v in (0, 6, 0xffff):
            with self.subTest(kind='count', value=v):
                with self.assertRaises(IndexError):
                    self.run_guard('count', 5, v)
        for v in (1, 3, 5):
            self.run_guard('count', 5, v)
        for v in (0, 4, 0xffff):
            with self.subTest(kind='index', value=v):
                with self.assertRaises(IndexError):
                    self.run_guard('index', 0x8000, v)
        for v in (1, 3):
            self.run_guard('index', 0x8000, v)


if __name__ == '__main__':
    unittest.main()

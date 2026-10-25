"""Native-budget string DIM on original tokenized Spectrum BASIC."""
from __future__ import annotations
import os
from pathlib import Path
import sys
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from native_dynamic_string_dim import with_bounded_string_dims
from native_budgeted_string_dim import with_budgeted_string_dims, unproved_string_dims
from native_dynamic_dim import with_bounded_dynamic_dims
from native_budgeted_dim import with_budgeted_numeric_dims

FRONTEND = Path(os.environ['RBC_TEST_FRONTEND']) if os.environ.get('RBC_TEST_FRONTEND') else None
TAPE = Path(os.environ['RBC_TEST_HISOFT_TAPE']) if os.environ.get('RBC_TEST_HISOFT_TAPE') else None
ROM = Path(os.environ['RBC_TEST_ROM']) if os.environ.get('RBC_TEST_ROM') else None
READY = bool(FRONTEND and (FRONTEND / 'compiler.py').is_file()
             and TAPE and TAPE.is_file() and ROM and ROM.is_file())
if READY:
    sys.path.insert(0, str(FRONTEND))
    import compiler, hbcimage, source
    from basic_listing import encode_strict_listing
    from z80asm import asm
    from z80mini import Z80


class TokenInspection(unittest.TestCase):
    def test_only_real_one_dimension_string_arrays(self):
        lines=[(10,b'\xee L:\xe9 B$(L):\xe9 C$(L):\xe9 Q(L)\r'),
               (20,b'\xf5 "DIM X$(L)":\xea DIM Y$(L)\r'),
               (30,b'\xe9 D$(4,3)\r')]
        self.assertEqual(unproved_string_dims(lines,{}),{1:1,2:1})
        self.assertEqual(unproved_string_dims(lines,{1:(b'l',3)}),{2:1})

    def test_unsafe_and_mixed_declarations_remain_unhandled(self):
        for body in [b'\xe9 B$(L):\xe9 B$(2,4)\r',
                     b'\xe9 B$(L):\xe9 B$(5)\r',
                     b'\xe9 B$(L*L)\r',
                     b'\xe9 B$(USR 42)\r']:
            with self.subTest(body=body):
                self.assertEqual(unproved_string_dims([(10,body)],{}),{})


@unittest.skipUnless(READY, 'requires the original 48K ROM and HiSoft tape')
class NativeBudgetedStrings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()
        cls.image = hbcimage.Image.from_tape(TAPE)
        cls.kw = source.Keywords(cls.rom)
        base = with_bounded_dynamic_dims(compiler.Compiler,
                real_type=compiler.REAL, memfill_rt=compiler.RT.MEM_FILL)
        base = with_budgeted_numeric_dims(base, capacity=48,
                real_type=compiler.REAL, memfill_rt=compiler.RT.MEM_FILL)
        base = with_bounded_string_dims(base,
                string_type=compiler.STRING, memfill_rt=compiler.RT.MEM_FILL)
        cls.backend = with_budgeted_string_dims(base,capacity=48)

    def compile(self,listing):
        obj = self.backend(self.image,self.rom)
        program = encode_strict_listing(listing)
        program = source.add_directives(program,[],True,[],self.kw,obj.fp)
        tokens = source.tokenize_directives(program,self.kw)
        return obj,obj.compile_whole(tokens),tokens

    def test_input_owned_string_dims_and_numeric_array(self):
        listing = ('10 INPUT A$: LET L=LEN A$\n'
                   '20 DIM B$(L): DIM C$(L): DIM Q(L)\n'
                   '30 LET B$(1)=A$(1): LET Q(1)=3\n'
                   '40 PRINT C$(1 TO L)\n')
        obj,result,source_bytes=self.compile(listing)
        self.assertTrue(result.ok,(result.error,result.detail))
        self.assertEqual(obj._zxux_budgeted_string_dims,frozenset({1,2}))
        self.assertEqual(obj._zxux_budgeted_dims,frozenset({16}))
        self.assertEqual(obj.strvars[1]['last'],48)
        self.assertEqual(obj.strvars[2]['last'],48)
        self.assertEqual(obj.arrays[16]['last'],48)
        self.assertEqual(source_bytes,self.compile(listing)[2])

    def test_repeat_dim_clears_live_string(self):
        obj,result,_=self.compile('10 INPUT N: DIM B$(N)\n20 LET B$="HELLO"\n30 INPUT N: DIM B$(N)\n40 PRINT LEN B$\n')
        self.assertTrue(result.ok,(result.error,result.detail))
        self.assertEqual(obj._zxux_budgeted_string_dims,frozenset({1}))

    def test_guard_on_original_runtime_length(self):
        code=[]
        class Stub:
            def emit(self, instr, *args):
                code.extend(asm(instr,*args))
        obj=with_bounded_string_dims(Stub,string_type=0,memfill_rt=0)()
        obj._zxux_bound_guard(48)
        machine=bytes(code)+b'\xc9'
        for value in (0,1,48,49,65535):
            with self.subTest(value=value):
                memory=bytearray(65536)
                memory[0x7000:0x7000+len(machine)]=machine
                cpu=Z80(memory)
                cpu.sp=0x9000
                cpu.hl=value
                cpu.hooks[8]=lambda _: (_ for _ in ()).throw(IndexError('size'))
                if 1<=value<=48:
                    cpu.call(0x7000)
                    self.assertEqual(cpu.hl,value)
                else:
                    with self.assertRaises(IndexError):cpu.call(0x7000)

if __name__ == '__main__':unittest.main()

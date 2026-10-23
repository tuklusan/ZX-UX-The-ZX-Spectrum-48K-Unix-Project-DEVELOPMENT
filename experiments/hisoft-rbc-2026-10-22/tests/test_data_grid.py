"""Tests on the preserved Morse Tutor tape and conservative failure cases."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'stage'))
from data_grid import adapt_numeric_data_grid

TOKENS = {0xE3:'READ',0xE4:'DATA',0xE5:'RESTORE',0xE9:'DIM',0xEA:'REM',
          0xEB:'FOR',0xF1:'LET',0xF3:'NEXT',0xCC:'TO',0xEC:'GO TO',0xED:'GO SUB'}

class KW:
    TOKEN=TOKENS
    CODE_FOR={text:token for token,text in TOKENS.items()}

class Tap:
    def split_lines(self, program):
        if isinstance(program, list):
            return program
        rows=[]; pos=0
        while pos<len(program):
            n=int.from_bytes(program[pos:pos+2], 'big')
            length=int.from_bytes(program[pos+2:pos+4], 'little')
            rows.append((n,program[pos+4:pos+4+length]))
            pos+=4+length
        assert pos == len(program)
        return rows

    def join_lines(self,rows):
        if isinstance(rows,list):
            return list(rows)
        return list(rows)

class Source:
    @staticmethod
    def hide_numbers(b,fp):
        n=int(b)
        assert 0<=n<65536
        return b+b'\x0e\x00\x00'+n.to_bytes(2,'little')+b'\x00'


def read_tzx(path):
    b=path.read_bytes()
    assert b.startswith(b'ZXTape!\x1a')
    pos=10;payload=[]
    while pos<len(b):
        assert b[pos] == 0x10
        length=int.from_bytes(b[pos+3:pos+5], 'little')
        payload.append(b[pos+5:pos+5+length]);pos+=5+length
    assert payload[0][0]==0 and payload[1][0]==255
    return payload[1][1:-1]

ROOT=Path(__file__).resolve().parents[3] / 'src/bonus/60-programs/38-morse-tutor/BASIC/38-morse-tutor.tzx'

class GridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=Tap().split_lines(read_tzx(ROOT))

    def adapt(self,source=None):
        return adapt_numeric_data_grid(self.original if source is None else source,KW(),None,Source(),Tap())

    def test_source_archive_present(self):
        self.assertTrue(ROOT.is_file())
        self.assertGreater(len(self.original),100)

    def test_dynamic_numeric_data_replaced(self):
        lines,proof=self.adapt()
        self.assertEqual(len(proof),1)
        self.assertEqual((proof[0]['array'],proof[0]['rows'],proof[0]['columns']),('c',36,5))
        self.assertEqual(proof[0]['fields'],180)
        self.assertEqual(proof[0]['scalar_inputs'],['l','s'])
        out=dict(lines)
        self.assertEqual(out[9060],b'\xea\r')
        self.assertEqual(out[9070],b'\xea\r')
        self.assertIn(b'\xe5' ,out[9090])
        self.assertEqual(len([n for n in out if 9010<=n<=9045]),36)
        self.assertTrue(any(b'=s' in out[n] for n in range(9010,9046)))
        self.assertTrue(any(b'=l' in out[n] for n in range(9010,9046)))
        self.assertEqual(out[9050].count(b'\xf1'),2)
        # Unrelated data and the remainder of the BASIC input are untouched.
        self.assertEqual(out[9110],dict(self.original)[9110])
        self.assertEqual(out[9000],dict(self.original)[9000])

    def test_changed_speeds_evaluated_at_runtime(self):
        new,_=self.adapt();out=dict(new)
        self.assertTrue(any(b'=s' in out[n] for n in range(9010,9046)))
        self.assertTrue(any(b'=l' in out[n] for n in range(9010,9046)))
        self.assertNotIn(b'=0',b''.join(out[n] for n in range(9010,9046)))

    def test_mismatched_data_count_no_change(self):
        original=[(n, (b'\xe4s,l\r' if n==9070 else b)) for n,b in self.original]
        same,proof=self.adapt(original)
        self.assertFalse(proof)
        self.assertEqual(same,original)

    def test_incoming_jump_no_change(self):
        original=[(n, (b'\xec 9030\r' if n==8500 else b)) for n,b in self.original]
        same,proof=self.adapt(original)
        self.assertFalse(proof)
        self.assertEqual(same,original)

    def test_unknown_expression_no_change(self):
        original=[(n, b'\xe4s+1,l\r' if n==9070 else b) for n,b in self.original]
        same,proof=self.adapt(original)
        self.assertFalse(proof)
        self.assertEqual(same,original)


if __name__=='__main__':unittest.main()
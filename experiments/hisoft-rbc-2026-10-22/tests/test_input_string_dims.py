"""Use the archived Anagrammatic tape, not a reconstructed listing."""
import hashlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'stage'))
from input_string_dims import adapt_input_string_dims

TOKEN = {0xee:'INPUT',0xfa:'IF',0xcb:'THEN',0xec:'GO TO',0xf1:'LET',
         0xb1:'LEN',0xeb:'FOR',0xcc:'TO',0xf3:'NEXT',0xe9:'DIM',
         0xc9:'<>',0xc7:'<=',0xc8:'>=',0xc5:'OR',0xba:'INT',
         0xed:'GO SUB',0xf5:'PRINT',0xfe:'RETURN'}
class KW:
    TOKEN = TOKEN
    CODE_FOR = {v:k for k,v in TOKEN.items()}
class Tap:
    @staticmethod
    def split_lines(program):
        if isinstance(program, list):
            return list(program)
        pos=0; rows=[]
        while pos < len(program):
            line = int.from_bytes(program[pos:pos+2],'big')
            length = int.from_bytes(program[pos+2:pos+4],'little')
            rows.append((line, program[pos+4:pos+4+length]))
            pos += 4+length
        assert pos == len(program)
        return rows
    @staticmethod
    def join_lines(rows):
        return list(rows)
class Source:
    @staticmethod
    def hide_numbers(raw, _fp):
        n = int(raw)
        return raw + b'\x0e\x00\x00' + n.to_bytes(2,'little') + b'\x00'

ROOT = Path(__file__).resolve().parents[3]/'src/bonus/60-programs/51-anagrammatic/BASIC/51-anagrammatic.tzx'

def original_rows():
    binary=ROOT.read_bytes()
    assert hashlib.sha256(binary).hexdigest() == '55c33e31b3e0256fca660b7cec280a6ac5c1fde6070d5737038a8a46d4690b81'
    assert binary.startswith(b'ZXTape!\x1a')
    offset=10; blocks=[]
    while offset<len(binary):
        assert binary[offset]==0x10
        n=int.from_bytes(binary[offset+3:offset+5],'little')
        blocks.append(binary[offset+5:offset+5+n]);offset+=5+n
    assert len(blocks)==2
    return Tap.split_lines(blocks[1][1:-1])

class TestInputStringDims(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=original_rows()
    def adapt(self, rows=None):
        return adapt_input_string_dims(self.rows if rows is None else rows,
                                       KW(),None,Source(),Tap())
    def test_preserved_tape_only_dim_changes(self):
        rewritten, proof=self.adapt()
        self.assertEqual([x['capacity'] for x in proof],[255])
        self.assertEqual([n for n,b in self.rows if dict(rewritten)[n]!=b],[270])
        self.assertEqual(dict(rewritten)[270].count(b'255\x0e'),3)
    def test_changed_input_length_proof_blocks_rewrite(self):
        rows=[(n,b.replace(bytes([0xb1])+b'A$',b'10\x0e\x00\x00\x0a\x00\x00') if n==160 else b) for n,b in self.rows]
        self.assertFalse(self.adapt(rows)[1])
    def test_additional_index_blocks_rewrite(self):
        self.assertFalse(self.adapt(self.rows+[(520,b'\xf1Q(256)=3\r')])[1])
    def test_extra_length_assignment_blocks_rewrite(self):
        self.assertFalse(self.adapt(self.rows+[(150,b'\xf1L=999\r')])[1])
    def test_altered_dim_rejected(self):
        rows=[(n,b.replace(b'Q(L)',b'Q(100)') if n==270 else b) for n,b in self.rows]
        self.assertFalse(self.adapt(rows)[1])
    def test_non_matching_program_untouched(self):
        candidate=[(10,b'\xf5"HELLO"\r')]
        original,proof=self.adapt(candidate)
        self.assertEqual(original,candidate)
        self.assertFalse(proof)
if __name__=='__main__':unittest.main()
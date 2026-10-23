"""Check compiler-side RESTORE/DATA resolution with original token layout."""
import struct
import sys
import types
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from restore_data import resolve_restores

TOK={'RESTORE':0xe5,'DATA':0xe4,'REM':0xea}

def join_lines(rows):
    return b''.join(bytes([n>>8,n&255])+struct.pack('<H',len(v))+v for n,v in rows)

def split_lines(program):
    p=0;out=[]
    while p+4<=len(program):
        n=program[p]*256+program[p+1]
        z=program[p+2]|program[p+3]<<8
        out.append((n,program[p+4:p+4+z]));p+=4+z
    return out

class RestoreTest(unittest.TestCase):
    def work(self,lines):
        original=join_lines(lines)
        mock_modules={
            'tap':types.SimpleNamespace(split_lines=split_lines,join_lines=join_lines),
            'source':types.SimpleNamespace(
                hide_numbers=lambda b,fp:b+b'\x0e\x00\x00\x00\x00\x00')}
        with patch.dict(sys.modules,mock_modules):
            result,changed=resolve_restores(original,types.SimpleNamespace(CODE_FOR=TOK),None)
        return split_lines(result), changed

    def test_real_exocet_self_reference(self):
        rows,change=self.work([
            (5,b'\xec9000\r'),
            (9000,b'\xe5' + b'9000\x0e\x00\x00\x00\x00\x00' + b':\xebx=0\r'),
            (9010,b'\xe3g\r'),
            (9040,b'\xe4 1,2,3\r')])
        self.assertEqual(change,[(9000,9000,9040)])
        self.assertIn(b'9040\x0e',dict(rows)[9000])

    def test_exact_data_target_unchanged(self):
        original=[(10,b'\xe5 100\r'),(100,b'\xe4 1,2\r')]
        rows,changed=self.work(original)
        self.assertEqual(rows,original)
        self.assertEqual(changed,[])

    def test_quoted_and_comment_text_not_modified(self):
        original=[(10,b'\xf5"RESTORE 9000":\xea RESTORE 9000\r'),
                  (9000,b'\xe5 9000\r'),(9010,b'\xe4 1\r')]
        rows,changes=self.work(original)
        self.assertEqual(changes,[(9000,9000,9010)])
        self.assertEqual(rows[0],original[0])

    def test_absent_data_not_rewritten(self):
        original=[(10,b'\xe5 9999\r'),(100,b'\xe4 1\r')]
        rows,changed=self.work(original)
        self.assertEqual(rows,original)
        self.assertEqual(changed,[])

    def test_no_number_restores_all_data(self):
        original=[(10,b'\xe5\r'),(100,b'\xe4 1\r')]
        rows,changed=self.work(original)
        self.assertEqual(rows,original)
        self.assertFalse(changed)

if __name__=='__main__':unittest.main()
"""Focused checks for the temporary ROM scroll-count adaptation."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import struct
import sys
import types
import unittest
from unittest.mock import patch

SRC = Path(__file__).resolve().parent.parent/'stage'/'native_scroll.py'
spec = importlib.util.spec_from_file_location('native_scroll',SRC)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

POKE=244
REM=234

class Keywords:
    CODE_FOR={'POKE':POKE,'REM':REM}


def split_lines(data):
    pos=0
    rows=[]
    while pos<len(data):
        n=int.from_bytes(data[pos:pos+2],'big')
        length=int.from_bytes(data[pos+2:pos+4],'little')
        rows.append((n,data[pos+4:pos+4+length]))
        pos+=4+length
    return rows


def join_lines(rows):
    return b''.join(n.to_bytes(2,'big')+struct.pack('<H',len(body))+body for n,body in rows)


class ScrollTests(unittest.TestCase):
    def update(self,lines):
        tap=types.ModuleType('tap')
        tap.split_lines=split_lines
        tap.join_lines=join_lines
        old=join_lines(lines)
        with patch.dict(sys.modules,{'tap':tap}):
            result,changed=module.adapt_scroll_counter(old,Keywords())
        self.assertEqual(old,join_lines(lines))
        return split_lines(result),changed

    def test_remove_only_plain_literal_in_middle(self):
        body=b'FOR f=1 TO 20:'+bytes([POKE])+b' 23692'+b'\x0e'+bytes(5)+b',255'+b'\x0e'+bytes(5)+b':PRINT "OK"\r'
        rows,changed=self.update([(9570,body)])
        self.assertEqual(rows,[(9570,b'FOR f=1 TO 20:PRINT "OK"\r')])
        self.assertEqual(changed,[9570])

    def test_keep_jump_line_if_only_statement_removed(self):
        rows,changed=self.update([(100,bytes([POKE])+b'23692,255\r')])
        self.assertEqual(rows,[(100,bytes([REM])+b'\r')])
        self.assertEqual(changed,[100])

    def test_no_change_to_other_system_addresses(self):
        for code in [b'23658,255',b'23692,0',b'23692,-1',b'23692,X',b'23700,255']:
            src=bytes([POKE])+code+b'\r'
            rows,changed=self.update([(10,src)])
            self.assertEqual(rows,[(10,src)])
            self.assertEqual(changed,[])

    def test_keep_conditional_and_quoted_text(self):
        src=b'IF Z=1 THEN '+bytes([POKE])+b'23692,255:PRINT "x:y"\r'
        rows,changed=self.update([(40,src)])
        self.assertEqual(rows,[(40,src)])
        self.assertEqual(changed,[])
        src=b'PRINT "POKE 23692,255":'+bytes([REM])+b' POKE 23692,255\r'
        rows,changed=self.update([(50,src)])
        self.assertEqual(rows,[(50,src)])
        self.assertEqual(changed,[])

    def test_multiple_standalone_statements(self):
        one=bytes([POKE])+b'23692,255'
        src=one+b':'+one+b':PRINT "AFTER"\r'
        rows,changed=self.update([(77,src)])
        self.assertEqual(rows,[(77,b'PRINT "AFTER"\r')])
        self.assertEqual(changed,[77,77])

if __name__=='__main__': unittest.main()
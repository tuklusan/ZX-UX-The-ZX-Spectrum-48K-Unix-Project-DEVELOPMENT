"""Offline, static proof of the experimental boot-only turbo receiver.

This is NOT a real-time FUSE boot proof; physical tape acceptance remains
outside these tests until the ROM and pilot routines are validated.
"""
from __future__ import annotations
import binascii
import importlib.util
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT/'release/build'

import sys
sys.path.insert(0,str(BUILD))
import turbo_boot_build as b
import turbo_segments as t

class TurboBootstrapContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = BUILD/'tmp/build'
        cls.tzx_path = cls.output/'ZX-UX.tzx'
        if not cls.tzx_path.exists():
            raise unittest.SkipTest('fresh provisional Z80 build needed')
        cls.data = cls.tzx_path.read_bytes()
        cls.image = (cls.output/'merged-image.bin').read_bytes()

    def test_compact_container_under_30000_bytes(self):
        self.assertLess(len(self.data), 30000)
        self.assertLessEqual(len(self.image), len(self.data))

    def blocks(self):
        data = self.data
        self.assertEqual(data[:10],b'ZXTape!\x1a\x01\x14')
        pos=10
        standard=[]
        turbo=[]
        while pos < len(data):
            ty=data[pos];pos+=1
            if ty == 0x10:
                pause,n = struct.unpack_from('<HH',data,pos); pos+=4
                item=data[pos:pos+n];pos+=n
                self.assertEqual(len(item),n)
                self.assertEqual(t.xor_bytes(item),0)
                standard.append((pause,item))
            elif ty == 0x11:
                timing=struct.unpack_from('<6H',data,pos);pos+=12
                used_bits=data[pos];pos+=1
                pause=struct.unpack_from('<H',data,pos)[0];pos+=2
                n=int.from_bytes(data[pos:pos+3],'little');pos+=3
                item=data[pos:pos+n];pos+=n
                self.assertEqual(len(item),n)
                self.assertEqual(timing,t.TIMINGS)
                self.assertEqual(used_bits,8)
                turbo.append((pause,item))
            else:
                self.fail(f'not a compact pulse-timing/data record: {ty:02X}')
        self.assertEqual(pos,len(data))
        return standard,turbo

    def test_4_standard_and_24_turbo_records(self):
        standard,turbo = self.blocks()
        self.assertEqual(len(standard),4)
        self.assertEqual(len(turbo),24)
        self.assertEqual([p for p,_ in standard],[1000,1000,1000,1500])
        self.assertEqual({p for p,_ in turbo},{400})

    def test_separate_rom_basic_and_bootstrap(self):
        standard,_=self.blocks()
        bas_header,bas_data,code_header,code_data=[body for _,body in standard]
        self.assertEqual(bas_header[1],0)
        self.assertEqual(code_header[1],3)
        self.assertEqual(int.from_bytes(code_header[14:16],'little'),0xd000)
        self.assertEqual(int.from_bytes(code_header[12:14],'little'),len(code_data)-2)
        basic=bas_data[1:-1]
        self.assertIn(b'52991',basic)
        self.assertIn(b'53248',basic)
        self.assertEqual(basic.count(b'\xef""\xaf'),1)
        self.assertTrue(code_data[1:-1].startswith(b'\xf3\x31\xff\xce'))
        self.assertEqual(code_data[1:-1],(self.output/'turbo_boot.bin').read_bytes())

    def test_24_packets_reconstruct_exact_build_image(self):
        _,turbo=self.blocks()
        offsets=t.layout(len(self.image))
        self.assertEqual(len(offsets),24)
        got=bytearray()
        for index,((offset,size),(_,data)) in enumerate(zip(offsets,turbo),1):
            self.assertEqual(data[:4],b'ZX\x01'+bytes([index]))
            self.assertEqual(struct.unpack('<HH',data[4:8]),(offset,size))
            self.assertEqual(binascii.crc_hqx(data[:-3],0xffff),int.from_bytes(data[-3:-1],'little'))
            self.assertEqual(t.xor_bytes(data),0)
            got.extend(data[8:-3])
        self.assertEqual(bytes(got),self.image)

    def test_line_fact_width_and_independent_rom(self):
        syms={}
        for line in (BUILD/'tmp/src/unix.sym').read_text().splitlines():
            m = re.match(r'(\S+): EQU 0x([0-9A-Fa-f]+)',line)
            if m:syms[m.group(1)]=int(m.group(2),16)
        _,_,free,_=b.osbuild.mkfs(syms,b.osbuild.program_list())
        lines=b.progress_lines(len(self.image),syms,syms['kend']-0x6000,free)
        self.assertEqual(len(lines),24)
        self.assertEqual({len(line) for line in lines},{32})
        self.assertIn('kernel limit: 8192 bytes',''.join(lines))
        self.assertIn('default time: 09:00:00',''.join(lines))
        self.assertIn(''.join(b.expanded_line(line) for line in lines).encode(),
                      (self.output/'turbo_boot.bin').read_bytes())

    def test_single_compact_shipped_tzx(self):
        shipped=(ROOT/'release/dist/zx-ux/ZX-UX.tzx').read_bytes()
        # After an offline build the candidate is promoted only after checks.
        self.assertEqual(len(shipped),len(self.data))
        self.assertTrue(shipped == self.data)
        self.assertLess(len(shipped),30_000)
        self.assertIn(b'ZX\x01\x01\x00\x00',shipped)

if __name__ == '__main__':
    unittest.main()

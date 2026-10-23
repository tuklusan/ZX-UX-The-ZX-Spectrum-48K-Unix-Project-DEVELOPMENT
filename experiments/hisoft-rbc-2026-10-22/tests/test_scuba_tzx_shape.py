"""Match RBC's Scuba font exception to the untouched original tape.

This checks the real tokenized listing, rather than a hand-built facsimile.
Unsupported tape blocks and malformed line lengths are never skipped.
"""
import sys
import unittest
from pathlib import Path
from struct import unpack_from

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'stage'))
from scuba_charset import _shape, _ORIGINAL

TOKENS = {
    0xAC:'AT', 0xBE:'PEEK', 0xC0:'USR', 0xCB:'THEN', 0xCC:'TO', 0xD9:'INK',
    0xDA:'PAPER', 0xDD:'INVERSE', 0xE3:'READ', 0xE4:'DATA',
    0xE5:'RESTORE', 0xE7:'BORDER', 0xEA:'REM', 0xEB:'FOR',
    0xEC:'GO TO', 0xF3:'NEXT', 0xF4:'POKE', 0xF5:'PRINT',
    0xFA:'IF', 0xFB:'CLS', 0xFE:'RETURN',
}


def original_lines(tzx: bytes):
    if not tzx.startswith(b'ZXTape!\x1a') or len(tzx) < 10:
        raise ValueError('invalid original tape header')
    pos = 10
    programs = []
    while pos < len(tzx):
        kind = tzx[pos]
        pos += 1
        if kind != 0x10:
            raise ValueError('unexpected block in original Scuba tape')
        if pos + 4 > len(tzx):
            raise ValueError('truncated cassette block header')
        _, size = unpack_from('<HH', tzx, pos)
        pos += 4
        if pos + size > len(tzx):
            raise ValueError('truncated cassette block payload')
        data = tzx[pos:pos + size]
        pos += size
        checksum = 0
        for byte in data:
            checksum ^= byte
        if checksum:
            raise ValueError('bad cassette checksum')
        if data[0] == 0xFF:
            programs.append(data[1:-1])
    if len(programs) != 1:
        raise ValueError('expected one BASIC code block')
    program = programs[0]
    result = []
    pos = 0
    while pos < len(program):
        if pos + 4 > len(program):
            raise ValueError('incomplete BASIC line header')
        line = int.from_bytes(program[pos:pos+2], 'big')
        count = int.from_bytes(program[pos+2:pos+4], 'little')
        pos += 4
        body = program[pos:pos+count]
        pos += count
        if len(body) != count or not body.endswith(b'\r'):
            raise ValueError('invalid BASIC line payload')
        result.append((line, body))
    return result


class ArchivedTape(unittest.TestCase):
    def test_exact_archived_scuba_shape(self):
        root = HERE.parents[1]
        source = root / 'src/bonus/60-programs/14-scuba/BASIC/14-scuba.tzx'
        lines = original_lines(source.read_bytes())
        self.assertEqual(len(lines), 202)
        self.assertTrue(_shape(lines, TOKENS, False))
        self.assertEqual(_ORIGINAL[5], 'POKE23658,255:')

    def test_rejects_bad_tape(self):
        with self.assertRaises(ValueError):
            original_lines(b'corrupt')


if __name__ == '__main__':
    unittest.main()

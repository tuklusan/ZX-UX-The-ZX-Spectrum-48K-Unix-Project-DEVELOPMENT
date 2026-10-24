"""USR token ban and permitted UDG POKE targets."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from safety_usr import UnsupportedUsr, enforce_numeric_usr

TOK = {0xc0: 'USR', 0xf4: 'POKE', 0xeb: 'FOR', 0xcc: 'TO', 0xf3: 'NEXT',
       0xea: 'REM', 0xf5: 'PRINT', 0xf1: 'LET', 0xf9: 'RANDOMIZE'}


def tokens(s):
    for label, number in (('USR', 0xc0), ('POKE', 0xf4), ('FOR', 0xeb),
                          ('TO', 0xcc), ('NEXT', 0xf3), ('REM', 0xea),
                          ('PRINT', 0xf5), ('LET', 0xf1), ('RANDOMIZE', 0xf9)):
        s = s.replace('{' + label + '}', chr(number))
    return s.encode('latin1')


def proof(line, expr, *offsets):
    return {'line': line, 'expression': expr,
            'addresses': [{'space': 'process_udg', 'offset': n} for n in offsets]}


class UsrGate(unittest.TestCase):
    def check(self, body, proofs=()):
        enforce_numeric_usr([(10, tokens(body))], [], list(proofs), TOK)

    def test_udg_poke_is_permitted(self):
        self.check('{POKE} {USR} "b"+8,1', [proof(10, 'USR  "b"+8', 16)])

    def test_numeric_usr_rejected(self):
        for body in ('{RANDOMIZE} {USR} 32768', '{LET} X={USR} 3280',
                     '{POKE} {USR} 32768,1'):
            with self.subTest(body=body), self.assertRaises(UnsupportedUsr):
                self.check(body)

    def test_graphics_outside_poke_rejected(self):
        with self.assertRaises(UnsupportedUsr):
            self.check('{LET} X={USR} "a"')

    def test_unproved_graphics_poke_rejected(self):
        with self.assertRaises(UnsupportedUsr):
            self.check('{POKE} {USR} "a"+X,1')

    def test_quoted_and_rem_ignored(self):
        self.check('{PRINT} "USR":{REM} {USR} 30000')
        self.check('{PRINT} "' + chr(0xc0) + '"')

    def test_out_of_range_proof_rejected(self):
        with self.assertRaises(UnsupportedUsr):
            self.check('{POKE} {USR} "u"+8,1', [proof(10, 'USR  "u"+8', 168)])


if __name__ == '__main__':
    unittest.main()

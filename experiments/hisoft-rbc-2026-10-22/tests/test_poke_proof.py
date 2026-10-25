"""Ordinary POKE responsibility, UDG finite proofs, and USR prohibition."""
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from poke_proof import prove_pokes, PokeAddressError
from safety_usr import enforce_numeric_usr, UnsupportedUsr

TOK={0xc0:'USR',0xf4:'POKE',0xeb:'FOR',0xcc:'TO',0xf3:'NEXT',0xfa:'IF',
     0xec:'GO TO',0xf1:'LET',0xea:'REM'}


def tokens(text):
    for word, byte in (('USR',0xc0),('POKE',0xf4),('FOR',0xeb),('NEXT',0xf3),
                       ('TO',0xcc),('GO TO',0xec),('IF',0xfa),('LET',0xf1)):
        text=text.replace('{'+word+'}',chr(byte))
    return text.encode('latin-1')


def check(*text):
    lines=[(10+i*10,tokens(t)) for i,t in enumerate(text)]
    checks=[SimpleNamespace(line=n,operation='POKE') for n,b in lines
            for _ in range(b.count(b'\xf4'))]
    proof=prove_pokes(lines,TOK,checks)
    enforce_numeric_usr(lines,checks,proof,TOK)
    return proof


class PokePolicyTests(unittest.TestCase):
    def test_known_address(self):
        self.assertEqual(check('{POKE} 16384,255')[0]['addresses'],
                         [{'space':'absolute','offset':16384}])

    def test_dynamic_is_programmer_responsibility(self):
        self.assertEqual(check('{POKE} X,1')[0]['status'],
                         'dynamic_programmer_responsibility')

    def test_udg_edges(self):
        self.assertEqual(check('{POKE} {USR} "a",1')[0]['addresses'][0]['offset'],0)
        self.assertEqual(check('{POKE} {USR} "b"+8,1')[0]['addresses'][0]['offset'],16)
        self.assertEqual(check('{POKE} {USR} "u"+7,1')[0]['addresses'][0]['offset'],167)

    def test_udg_outside_168_bytes_rejected(self):
        with self.assertRaisesRegex(PokeAddressError,'E_UDG_RANGE'):
            check('{POKE} {USR} "u"+8,1')

    def test_udg_unknown_offset_runtime_guarded(self):
        self.assertEqual(check('{POKE} {USR} "a"+X,1')[0]['status'],
                         'runtime_guarded_udg_pointer')

    def test_bounded_udg_loop(self):
        proof=check('{FOR} F={USR} "a" {TO} {USR} "b"+7',
                    '{POKE} F,1','{NEXT} F')
        self.assertEqual(len(proof[0]['addresses']),16)

    def test_computed_line_jump_can_enter_single_line_bounded_for(self):
        proof=check('{GO TO} K',
                    '{FOR} C={USR} "a" {TO} {USR} "a"+7: READ V: {POKE} C,V: {NEXT} C')
        self.assertEqual([x['offset'] for x in proof[0]['addresses']],list(range(8)))

    def test_computed_jump_into_later_line_blocks_unproved_udg(self):
        with self.assertRaisesRegex(PokeAddressError,'computed branch could enter FOR body'):
            check('{GO TO} K',
                  '{FOR} C={USR} "a" {TO} {USR} "a"+7',
                  'READ V: {POKE} C,V: {NEXT} C')

    def test_machine_usr_rejected(self):
        with self.assertRaises(UnsupportedUsr):
            check('{LET} X={USR} 32768')

    def test_message_is_not_code(self):
        self.assertEqual(check('PRINT "POKE USR"'),[])


if __name__ == '__main__':
    unittest.main()

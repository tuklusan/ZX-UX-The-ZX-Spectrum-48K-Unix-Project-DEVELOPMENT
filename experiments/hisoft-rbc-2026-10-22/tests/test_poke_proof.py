"""Proof tests: exact targets, bounded loops, and unsafe control flow."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from types import SimpleNamespace
from poke_proof import PokeAddressError, prove_pokes


def prove(*rows):
    lines=[(i+10,text.encode('ascii')) for i,text in enumerate(rows)]
    # Count executable POKE operations, including multiple on one line.
    from audit_policy import scrub_code
    import re
    findings=[SimpleNamespace(line=i+10,operation='POKE')
              for i,text in enumerate(rows)
              for _ in re.finditer(r'\bPOKE\b',scrub_code(text),re.I)]
    return prove_pokes(lines,{},findings)


class PokeProofTests(unittest.TestCase):
    def test_literal_is_proved_independently_of_memory_policy(self):
        result=prove('POKE 23658,255')
        self.assertEqual(result[0]['addresses'],[{'space':'absolute','offset':23658}])
        # Proved target is still subject to the separate memory-policy gate.

    def test_nested_scuba_exact_104_addresses(self):
        results=prove('FOR K=0 TO 12:FOR J=0 TO 7:READ A:POKE 60256+(K+33)*8+J,A:NEXT J:NEXT K')
        got={p['offset'] for p in results[0]['addresses']}
        self.assertEqual(got,set(range(60520,60624)))

    def test_scuba_rom_copy_exact_768_addresses(self):
        results=prove('FOR X=256 TO 1023:POKE 60000+X,PEEK (15104+X):NEXT X')
        self.assertEqual([r['offset'] for r in results[0]['addresses']],list(range(60256,61024)))

    def test_relocatable_udg_exact_byte_set(self):
        results=prove('FOR F=USR "a" TO USR "g"+7:READ V:POKE F,V:NEXT F')
        self.assertEqual(results[0]['addresses'],[{'space':'process_udg','offset':x} for x in range(56)])

    def test_strided_set_has_gaps_not_range_envelope(self):
        results=prove('FOR X=100 TO 106 STEP 3:POKE X,0:NEXT X')
        self.assertEqual([v['offset'] for v in results[0]['addresses']],[100,103,106])

    def test_unbounded_user_variable_fails(self):
        with self.assertRaisesRegex(PokeAddressError,'no proved bounds'):
            prove('INPUT X:POKE X,1')

    def test_loop_index_mutation_fails(self):
        with self.assertRaisesRegex(PokeAddressError,'may be reassigned'):
            prove('FOR X=0 TO 7:LET X=USR "a":POKE X,0:NEXT X')

    def test_branch_into_loop_body_fails(self):
        with self.assertRaisesRegex(PokeAddressError,'bypass FOR'):
            prove('GO TO 12','FOR X=0 TO 7','POKE X,0','NEXT X')

    def test_unsafe_conditional_loop_body_fails(self):
        with self.assertRaisesRegex(PokeAddressError,'conditional FOR body'):
            prove('FOR X=0 TO 7','IF X=2 THEN PRINT "skip"','POKE X,0','NEXT X')

    def test_string_usr_not_executable_poke(self):
        self.assertEqual(prove('PRINT "POKE 50000,1"'),[])

    def test_unproved_chr_graphics_fails(self):
        with self.assertRaisesRegex(PokeAddressError,'USR argument'):
            prove('FOR X=0 TO 7:POKE USR CHR$ (143+M)+X,1:NEXT X')

    def test_unknown_relocation_base_rejected(self):
        with self.assertRaisesRegex(PokeAddressError,'unproved memory base'):
            prove('POKE USR "a"+USR "b",1')

if __name__=='__main__':unittest.main()

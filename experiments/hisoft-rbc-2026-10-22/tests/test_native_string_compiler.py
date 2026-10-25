import unittest
from native_string_compiler import with_static_strings

class Base:
    def reset(self,program):
        self.program=program
        self.strvars=[{'flags':0,'first':0,'last':0} for _ in range(26)]

def letter(x):
    return x - ord('a')

class Tests(unittest.TestCase):
    def test_capped_string(self):
        cls=with_static_strings(Base,[{'variable':'A$','max_chars':12}],letter)
        c=cls();c.reset(b'')
        self.assertEqual(c.strvars[0]['last'],12)
        c.reset(b'')
        self.assertEqual(c.strvars[0]['last'],12)
    def test_none_keeps_original_class(self):
        self.assertIs(with_static_strings(Base,[],letter), Base)
    def test_invalid_limit_rejected(self):
        for p in ([{'variable':'A$','max_chars':0}],[{'variable':'A$','max_chars':256}],
                  [{'variable':'ZZ$','max_chars':3}],
                  [{'variable':'A$','max_chars':4},{'variable':'a$','max_chars':7}]):
            with self.assertRaises(ValueError):
                with_static_strings(Base,p,letter)
    def test_all_other_variables_unchanged(self):
        c=with_static_strings(Base,[{'variable':'Z$','max_chars':5}],letter)()
        c.reset(b'')
        self.assertEqual([e['last'] for e in c.strvars[:25]],[0]*25)
        self.assertEqual(c.strvars[25]['last'],5)
if __name__=='__main__':unittest.main()

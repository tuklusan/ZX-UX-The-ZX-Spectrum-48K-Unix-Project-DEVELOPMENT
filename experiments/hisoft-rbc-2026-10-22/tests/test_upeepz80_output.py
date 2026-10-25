"""Verify native peephole chain never silently damages SSX relocations."""
import sys
import unittest
from pathlib import Path

STAGE=Path(__file__).resolve().parents[1]/'stage'
SDK=Path(__file__).resolve().parents[3]/'src/zx-ux-sdk'
sys.path.insert(0,str(STAGE))
sys.path.insert(0,str(SDK))
import ras
import rld
from upeepz80_output import optimize_ssx


class Identity:
    stats = {}
    def optimize(self, source):
        return source


class Change:
    stats = {"changed": 1}
    def optimize(self, source):
        return source.replace("    db 0", "    db 1", 1)


class PostLinkTests(unittest.TestCase):
    @staticmethod
    def fixture():
        asm = ("    section text\n    global start\nstart:\n"
               "    ld hl,vars\n    xor a\n    ret\n"
               "    section bss\nvars:\n    ds 4\n")
        obj=ras.assemble_text(asm,"fixture.s")
        ssx,*_=rld.link([rld.Obj(obj,"fixture")],[],"start",384,0)
        return ssx

    def test_full_relocation_preserving_assembly_relink(self):
        ssx=self.fixture()
        linked, report=optimize_ssx(ssx,rld,ras,Identity())
        self.assertEqual(linked,ssx)
        self.assertEqual(report["saved_file_bytes"],0)
        self.assertEqual(report["saved_memory_bytes"],0)
        self.assertEqual(report["input_sha256"],report["linked_sha256"])
        self.assertEqual(report["bss_bytes"],4)

    def test_changes_must_not_escape_without_relocation_proof(self):
        ssx=self.fixture()
        class Edit:
            stats={}
            def optimize(self,s):
                return s.replace("    db 33", "    db 34", 1)
        # There is a relocation before the xor; change its code byte.
        with self.assertRaisesRegex(ValueError,"cannot prove"):
            optimize_ssx(ssx,rld,ras,Edit())

    def test_invalid_native_format_rejected(self):
        with self.assertRaises(Exception):
            optimize_ssx(b"not-an-ssx",rld,ras,Identity())


if __name__=="__main__":
    unittest.main()

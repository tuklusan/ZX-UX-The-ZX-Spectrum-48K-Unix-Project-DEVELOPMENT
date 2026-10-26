"""Validate exact source words without decoding final executable bytes."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from symbolic_source_patches import (UnresolvedSourcePatch, from_emissions,
                                     verify_three_passes)


def pair(at, method, number):
    return [SimpleNamespace(kind='direct-write', position=at+i,
                            source=method, data=bytes(((number >> (8*i)) & 255,)))
            for i in (0, 1)]


class SourcePatches(unittest.TestCase):
    def make(self, base, length=3, bad=False):
        data = bytearray(48)
        payload = pair(1, 'emit_string_inline', length) + pair(
            10, 'st_next', (base + (40 if bad else 24)) & 65535)
        payload += pair(20, 'end_of_line', (base + 30) & 65535)
        for event in payload:
            data[event.position:event.position+1] = event.data
        return from_emissions(payload, bytes(data), base, 40)

    def test_real_source_categories_track_all_three_bases(self):
        bases = [0x6000, 0x6000-389, 0x6000-617]
        words = [self.make(base) for base in bases]
        report = verify_three_passes(words, [SimpleNamespace(base=b) for b in bases])
        self.assertEqual(report['verified_source_words'], 3)
        self.assertEqual(report['verified_patch_bytes'], 6)
        self.assertEqual(report['word_kinds'], {'literal-length': 1, 'control-target': 2})
        self.assertEqual(words[0][1].target, 24)

    def test_unknown_source_method_fails_closed(self):
        payload = pair(1, 'unknown_patch', 24)
        with self.assertRaises(UnresolvedSourcePatch):
            from_emissions(payload, bytes(48), 0, 40)

    def test_incomplete_patch_fails_closed(self):
        with self.assertRaises(UnresolvedSourcePatch):
            from_emissions(pair(1, 'st_next', 24)[:1], bytes(48), 0, 40)

    def test_two_byte_native_loop_replacement_is_typed(self):
        payload = [SimpleNamespace(kind='direct-write', position=11,
                                   source='spectrum_for', data=(0x5014).to_bytes(2, 'little'))]
        image = bytearray(64)
        image[11:13] = payload[0].data
        words = from_emissions(payload, bytes(image), 0x5000, 40)
        self.assertEqual(words[0].target, 20)

    def test_target_outside_text_fails_closed(self):
        with self.assertRaises(UnresolvedSourcePatch):
            self.make(0x6000, bad=True)

    def test_changed_length_is_not_relocation(self):
        bases = [0x6000, 0x5E7B, 0x5D97]
        words = [self.make(b, length=3 if i < 2 else 4)
                 for i,b in enumerate(bases)]
        with self.assertRaises(UnresolvedSourcePatch):
            verify_three_passes(words, [SimpleNamespace(base=b) for b in bases])

    def test_changed_target_is_not_relocation(self):
        bases = [0x6000, 0x5E7B, 0x5D97]
        words = [self.make(b) for b in bases]
        patched = list(words[2])
        patched[1] = patched[1].__class__(patched[1].site, patched[1].source,
                                        patched[1].kind, bases[2]+25, 25)
        with self.assertRaises(UnresolvedSourcePatch):
            verify_three_passes((words[0], words[1], tuple(patched)),
                                [SimpleNamespace(base=b) for b in bases])

if __name__ == '__main__':
    unittest.main()

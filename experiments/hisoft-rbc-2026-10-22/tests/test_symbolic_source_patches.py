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

    def test_rewound_inline_length_requires_full_later_typed_source(self):
        # Original HiSoft may discard the old inline length and overwrite it
        # with a new CALL mnemonic after rewinding the compiler's code cursor.
        base = 0x6000
        events = [SimpleNamespace(kind='word', position=1,
                                  source='(3,)', data=b'\x03\x00')]
        events += pair(1, 'emit_string_inline', 1)
        events += [SimpleNamespace(kind='opcode', position=0,
                                   source='call nn', data=b'\xcd'),
                   SimpleNamespace(kind='relocation', position=1,
                                   source='(3,)', data=b'\x03\x60')]
        self.assertEqual(from_emissions(events, b'\xcd\x03\x60\xc9', base, 4), ())
        # One byte of the old word remaining is not a complete typed rewrite.
        with self.assertRaisesRegex(UnresolvedSourcePatch, 'changed after capture'):
            from_emissions(events[:-1] + [SimpleNamespace(
                kind='byte', position=1, source='(3,)', data=b'\x03')],
                b'\xcd\x03\x00\xc9', base, 4)
        # An unknown later byte producer cannot make a stale patch safe.
        with self.assertRaisesRegex(UnresolvedSourcePatch, 'changed after capture'):
            from_emissions(events[:-1] + [SimpleNamespace(
                kind='runtime-opaque', position=1, source='unknown',
                data=b'\x03\x60')], b'\xcd\x03\x60\xc9', base, 4)
        # Incorrect final bytes cannot be accepted as a typed rewind either.
        with self.assertRaisesRegex(UnresolvedSourcePatch, 'changed after capture'):
            from_emissions(events, b'\xcd\x04\x60\xc9', base, 4)

    def test_replaced_loop_jump_patch_requires_new_full_source(self):
        base = 0x6000
        old = pair(1, 'spectrum_for', base + 4)
        new = pair(1, 'spectrum_pass', base + 3)
        replacement = SimpleNamespace(kind='instruction', position=0,
                                      source='jp nz,$FFFF', data=b'\xc2\xff\xff')
        final = b'\xc2' + (base + 3).to_bytes(2, 'little') + b'\xc9'
        words = from_emissions(old + [replacement] + new, final, base, 4)
        self.assertEqual([(w.site, w.source, w.target) for w in words],
                         [(1, 'spectrum_pass', 3)])
        with self.assertRaisesRegex(UnresolvedSourcePatch, 'overlapping'):
            from_emissions(old + new, final, base, 4)
        with self.assertRaisesRegex(UnresolvedSourcePatch, 'overlapping'):
            from_emissions(old + [SimpleNamespace(
                kind='opcode', position=0, source='jp nz,nn', data=b'\xc2')]
                + new, final, base, 4)
        with self.assertRaises(UnresolvedSourcePatch):
            from_emissions(old + [replacement] +
                           pair(1, 'unknown', base + 3), final, base, 4)

    def test_def_fn_skip_jump_is_real_native_control_word(self):
        bases = (0x6000, 0x5e7b, 0x5d97)
        groups = []
        for base in bases:
            image = bytearray(80)
            image[19:21] = (base + 51).to_bytes(2, 'little')
            groups.append(from_emissions(
                pair(19, 'st_deffn', base + 51), bytes(image), base, 75))
        report = verify_three_passes(groups,
                                    [SimpleNamespace(base=b) for b in bases])
        self.assertEqual(report['word_kinds'],
                         {'literal-length': 0, 'control-target': 1})
        self.assertTrue(all(group[0].target == 51 for group in groups))
        bad = bytearray(80)
        bad[19:21] = (0x6000 + 77).to_bytes(2, 'little')
        with self.assertRaisesRegex(UnresolvedSourcePatch, 'outside code'):
            from_emissions(pair(19, 'st_deffn', 0x6000 + 77),
                           bytes(bad), 0x6000, 75)

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

    def test_overlapping_patch_words_fail_even_when_bytes_agree(self):
        base = 0x5050
        # Both words have bytes 0x50,0x50. The overlapping site must not
        # be admitted merely because the final image still matches.
        payload = pair(10, 'st_next', base) + pair(11, 'st_next', base)
        image = bytearray(64)
        image[10:13] = bytes((0x50, 0x50, 0x50))
        with self.assertRaisesRegex(UnresolvedSourcePatch, 'overlapping'):
            from_emissions(payload, bytes(image), base, 40)

    def test_data_region_cannot_be_classified_as_code_patch(self):
        base = 0x6000
        payload = pair(46, 'st_next', base + 12)
        image = bytearray(64)
        image[46:48] = (base + 12).to_bytes(2, 'little')
        with self.assertRaisesRegex(UnresolvedSourcePatch, 'executable text'):
            from_emissions(payload, bytes(image), base, 40)

    def test_three_identical_bases_cannot_claim_relocation_proof(self):
        base = 0x6000
        with self.assertRaisesRegex(UnresolvedSourcePatch, 'distinct'):
            verify_three_passes([self.make(base)] * 3,
                                [SimpleNamespace(base=base)] * 3)

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

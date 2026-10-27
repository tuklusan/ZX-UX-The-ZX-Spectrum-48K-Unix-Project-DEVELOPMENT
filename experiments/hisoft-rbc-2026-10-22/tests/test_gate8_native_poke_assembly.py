"""Native relocation proof for source-owned RBC protected POKE handler."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]

import ras
import rld
from z80asm import asm
from native_sysvars_rt import _native_poke
from gate8_runtime_source_match import RuntimeMatchError, _verify_poke_source


class SourceOwnedPoke(unittest.TestCase):
    def check(self, base, entry, offset, total, font_alias):
        raw, source, sites = _native_poke(asm, offset, base, total,
                                          font_alias, entry, with_source=True)
        self.assertEqual(_native_poke(asm, offset, base, total, font_alias, entry), raw)
        obj = ras.assemble_text(source, 'native-poke.s')
        linked, *_ = rld.link([rld.Obj(obj, 'native-poke.sso')], [],
                              entry='start', stack=384)
        output = rld.parse_ssx(linked)
        self.assertEqual(output['relocs'], list(sites))
        self.assertEqual(output['bss'], 0)
        self.assertEqual(bytes(rld.relocate(output['image'], output['relocs'],
                                            base + entry)), raw)
        self.assertEqual(len(_verify_poke_source(raw, base, entry, {
            'sysvar_offset': offset, 'process_total': total,
            'font_alias': font_alias})[0]), 64)
        self.assertIn('rbc_local_chars_sync', source)
        self.assertIn('start+', source)
        return raw

    def test_native_source_relinks_at_three_realistic_code_bases(self):
        for base in (0x5800, 0x6000, 0x6400):
            with self.subTest(base=base):
                raw = self.check(base, 2400, 3000, 3350, None)
                self.assertEqual(len(raw), 382)

    def test_optional_font_alias_has_independent_native_source(self):
        raw = self.check(0x6000, 2400, 3000, 3350, 0x5c36)
        self.assertEqual(len(raw), 375)

    def test_bad_compiler_layout_or_modified_runtime_is_refused(self):
        raw = self.check(0x6000, 2400, 3000, 3350, None)
        correct = {'sysvar_offset': 3000, 'process_total': 3350,
                   'font_alias': None}
        for bad in ({**correct, 'process_total': 3351},
                    {**correct, 'sysvar_offset': 3001},
                    {**correct, 'font_alias': 0x5c36},
                    {**correct, 'sysvar_offset': True},
                    {**correct, 'font_alias': 65536}):
            with self.subTest(bad=bad):
                with self.assertRaises(RuntimeMatchError):
                    _verify_poke_source(raw, 0x6000, 2400, bad)
        for index in (0, 17, 152, 381):
            altered = bytearray(raw)
            altered[index] ^= 1
            with self.subTest(index=index):
                with self.assertRaisesRegex(RuntimeMatchError, 'emission differs'):
                    _verify_poke_source(bytes(altered), 0x6000, 2400, correct)


if __name__ == '__main__':
    unittest.main()

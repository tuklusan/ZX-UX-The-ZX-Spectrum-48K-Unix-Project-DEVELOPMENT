"""Typed process-private PEEK assembly and combined runtime source checks."""
from pathlib import Path
import os
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from z80asm import asm
from native_sysvars_rt import _native_peek, _native_poke, PEEK_RT, POKE_RT
from gate8_native_runtime_combined import _replacement_listing, RuntimeCombinedError
from gate8_runtime_source_match import _verify_poke_source, RuntimeMatchError


class SourceOwnedPeek(unittest.TestCase):
    def test_native_peek_relocation_and_link_match_real_emitter(self):
        for base, site, total, font in ((0x5d00, 2100, 7600, None),
                                        (0x6300, 5700, 8900, 0x7100),
                                        (0x6b00, 3000, 7000, 0x7200)):
            with self.subTest(base=base):
                settings = {'sysvar_offset': 6843, 'process_total': total,
                            'font_alias': font}
                raw, source, sites = _native_peek(
                    asm, settings['sysvar_offset'], base, total, font, site,
                    with_source=True)
                self.assertEqual(raw, _native_peek(
                    asm, settings['sysvar_offset'], base, total, font, site))
                obj = ras.assemble_text(source, 'peek-native.s')
                linked, *_ = rld.link([rld.Obj(obj, 'peek-native.sso')],
                                      [], entry='start', stack=384)
                parsed = rld.parse_ssx(linked)
                self.assertEqual(parsed['relocs'], list(sites))
                actual = bytes(rld.relocate(parsed['image'], parsed['relocs'],
                                            base + site))
                self.assertEqual(actual, raw)
                self.assertEqual(parsed['bss'], 0)
                report = _verify_poke_source(raw, base, site, settings, peek=True)
                self.assertEqual(report[1], len(sites))
                lines, relative = _replacement_listing(
                    PEEK_RT, site, base, settings, raw)
                self.assertEqual(relative, sites)
                self.assertIn('rbc_peek_entry:', lines)
                self.assertTrue(any('rbc_peek_local_' in line for line in lines))

    def test_native_peek_isolated_from_poke_labels(self):
        base = 0x6000
        settings = {'sysvar_offset': 4120, 'process_total': 8200,
                    'font_alias': None}
        peek = _native_peek(asm, 4120, base, 8200, None, 900)
        poke = _native_poke(asm, 4120, base, 8200, None, 900+len(peek))
        a, _ = _replacement_listing(PEEK_RT, 900, base, settings, peek)
        b, _ = _replacement_listing(POKE_RT, 900+len(peek), base, settings, poke)
        labels = [line for line in a+b if line.strip().endswith(':')]
        self.assertEqual(len(labels), len(set(labels)))

    def test_reject_unknown_sysvar_layout_or_changed_bytes(self):
        base = 0x6000
        settings = {'sysvar_offset': 4120, 'process_total': 8200,
                    'font_alias': None}
        raw = _native_peek(asm, 4120, base, 8200, None, 900)
        altered = bytes((raw[0] ^ 1,)) + raw[1:]
        with self.assertRaisesRegex(RuntimeCombinedError, 'source PEEK'):
            _replacement_listing(PEEK_RT, 900, base, settings, altered)
        with self.assertRaisesRegex(RuntimeMatchError, 'PEEK source emission'):
            _verify_poke_source(altered, base, 900, settings, peek=True)
        with self.assertRaisesRegex(RuntimeCombinedError, 'layout'):
            _replacement_listing(PEEK_RT, 900, base, {}, raw)

    def test_original_motocross_uses_both_typed_source_routines(self):
        variables = tuple(os.environ.get(k) for k in (
            'RBC_G8_CHECKPOINT', 'RBC_G8_FRONTEND', 'RBC_G8_TAPE',
            'RBC_G8_OPTIMIZER'))
        if not all(variables):
            self.skipTest('verified compiler, frontend and optimizer required')
        from gate8_full_source_audit import run
        game = '06-motocross'
        report = run(ROOT / 'src/bonus/60-programs' / game / 'BASIC' /
                     (game + '.bas'), Path(variables[0]), Path(variables[1]),
                     Path(variables[2]), ROOT / 'src/zx-ux-sdk/rom/48.rom')
        self.assertEqual(report['source_instructions']['source_historical_instruction_variation'], 1)
        self.assertEqual(report['original_runtime_source_match']['typed_replacement_routines_verified'],
                         [PEEK_RT, POKE_RT])
        self.assertTrue(report['native_runtime_region']['native_region_verified'])
        baseline = report['native_whole_source_baseline']
        self.assertTrue(baseline['native_whole_source_baseline_linked'])
        self.assertTrue(baseline['native_image_byte_exact'])
        self.assertTrue(baseline['native_whole_optimizer_candidate']['native_baseline_source_reassembled'])
        self.assertFalse(report['gate8_complete'])


if __name__ == '__main__':
    unittest.main()

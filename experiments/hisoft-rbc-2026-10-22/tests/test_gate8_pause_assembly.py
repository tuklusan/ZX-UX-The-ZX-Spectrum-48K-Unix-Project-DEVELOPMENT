"""Native PAUSE source is an exact, independently assembled source witness."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]

import ras
import rld
from z80asm import asm
from native_pause_rt import _pause_code, original_pause_source
from gate8_original_runtime_types import compiler_image
from gate8_runtime_source_match import (RuntimeMatchError, _verify_pause_source,
                                        verify_three_runtime_sources)


class NativePauseSource(unittest.TestCase):
    def test_native_assembler_emits_exact_runtime(self):
        expected = _pause_code(asm)
        raw, source = original_pause_source(asm)
        self.assertEqual(len(expected), 46)
        self.assertEqual(raw, expected)
        self.assertIn('jr z,rbc_pause_scan', source)
        self.assertIn('jr nz,rbc_pause_done', source)
        assembled = ras.assemble_text(source, 'source-pause.s')
        linked, *_ = rld.link([rld.Obj(assembled, 'source-pause.sso')], [],
                              entry='start', stack=384)
        result = rld.parse_ssx(linked)
        self.assertEqual(result['image'], expected)
        self.assertEqual(result['relocs'], [])
        self.assertEqual(result['bss'], 0)
        self.assertEqual(len(_verify_pause_source(expected)), 64)

    def test_corrupted_pause_source_is_rejected(self):
        expected = _pause_code(asm)
        for index in (0, 6, 20, 45):
            with self.subTest(index=index):
                changed = bytearray(expected)
                changed[index] ^= 1
                with self.assertRaisesRegex(RuntimeMatchError, 'PAUSE source emission'):
                    _verify_pause_source(bytes(changed))

    def test_bad_entry_identity_is_rejected(self):
        code = compiler_image(Path('/mnt/data/HiSoft_BASIC_v1.1_48K_compiler_only.tzx').read_bytes())
        rom = (ROOT / 'src/zx-ux-sdk/rom/48.rom').read_bytes()
        image = _pause_code(asm)
        bases = (0x6000, 0x6100, 0x6200)
        spans = [(SimpleNamespace(kind='runtime-opaque', source='RT55',
                                  start=0, end=len(image)),)] * 3
        report = verify_three_runtime_sources(code, rom, [image]*3, bases,
                                              spans, {55: 'native-pause'})
        self.assertEqual(report['typed_replacement_routines_verified'], [55])
        self.assertEqual(report['typed_replacement_source_bytes'], 46)
        self.assertEqual(report['replacement_source_bytes_untyped'], 0)
        self.assertFalse(report['native_behavior_verified'])
        with self.assertRaisesRegex(RuntimeMatchError, 'wrong routine'):
            verify_three_runtime_sources(code, rom, [image]*3, bases,
                [(SimpleNamespace(kind='runtime-opaque', source='RT43',
                                  start=0, end=len(image)),)] * 3,
                {43: 'native-pause'})


if __name__ == '__main__':
    unittest.main()

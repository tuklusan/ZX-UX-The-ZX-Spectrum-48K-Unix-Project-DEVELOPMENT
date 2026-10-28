"""Private runtime addresses move with the whole typed HiSoft source image."""
from pathlib import Path
from unittest.mock import patch
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from z80asm import asm
from native_sysvars_rt import PEEK_RT, POKE_RT, BSS_BYTES, _native_peek, _native_poke
from symbolic_capture import Emission
from gate8_whole_native_baseline import _source_program, WholeBaselineError

BASES = (0x6000, 0x7000, 0x8000)


def source_case(fn, routine, base, prefix, before_bss=7, after_bss=13):
    entry = prefix + 3
    length = len(fn(asm, 0, 0))
    text_end = entry + length
    raw_data = bytes.fromhex('ff 76 18')
    image_size = text_end + len(raw_data)
    bss_offset = image_size + before_bss
    process_total = bss_offset + BSS_BYTES
    bss = before_bss + BSS_BYTES + after_bss
    raw = fn(asm, bss_offset, base, process_total, None, entry)
    head = b'\x00' * prefix + b'\xc3' + (base+entry).to_bytes(2, 'little')
    image = head + raw + raw_data
    events = [Emission(pos, 'instruction', 'nop', b'\x00')
              for pos in range(prefix)]
    events.extend((Emission(prefix, 'opcode', 'jp nn', b'\xc3'),
                   Emission(prefix+1, 'relocation', str(entry), head[-2:], entry),
                   Emission(entry, 'runtime-opaque', f'RT{routine}', raw),
                   Emission(text_end, 'data-source', 'source data', raw_data)))
    settings = dict(sysvar_offset=bss_offset, process_total=process_total,
                    font_alias=None)
    return events, image, text_end, bss, settings


class NativeSysvarWholeBaseline(unittest.TestCase):
    def test_source_links_three_bases_after_text_and_bss_moves(self):
        for fn, routine in ((_native_peek, PEEK_RT), (_native_poke, POKE_RT)):
            for prefix in (0, 11):
                for base in BASES:
                    with self.subTest(fn=fn.__name__, prefix=prefix, base=base):
                        events, image, text_end, bss, settings = source_case(
                            fn, routine, base, prefix)
                        with patch('gate8_whole_native_baseline._original_sections', return_value=()):
                            source, report, _map, _bounds = _source_program(
                            events, image, base, text_end, bss, asm,
                            b'', b'', {routine: 'native-peek' if routine == PEEK_RT
                                        else 'native-poke'}, settings)
                        self.assertIn('rbc_sysvar_storage:', source)
                        self.assertIn('rbc_process_end:', source)
                        self.assertIn('rbc_process_end-1', source)
                        self.assertIn('ld de,start', source)
                        obj = ras.assemble_text(source, 'rbc-full-native-sysvars.s')
                        ssx, *_ = rld.link([rld.Obj(obj, 'rbc-full-native-sysvars.sso')],
                                           [], entry='start', stack=384)
                        parsed = rld.parse_ssx(ssx)
                        self.assertEqual(bytes(rld.relocate(parsed['image'],
                                                            parsed['relocs'], base)), image)
                        self.assertEqual(parsed['bss'], bss)
                        self.assertEqual(parsed['entry'], 0)
                        self.assertEqual(report['source_data_bytes'], 3)
                        self.assertGreaterEqual(len(parsed['relocs']), 30)

    def test_out_of_process_source_anchor_is_rejected(self):
        events, image, end, bss, settings = source_case(
            _native_poke, POKE_RT, BASES[0], 0)
        for changed in (dict(settings, sysvar_offset=len(image)-1),
                        dict(settings, process_total=len(image)+bss+1),
                        dict(settings, process_total=settings['sysvar_offset']+13)):
            with self.subTest(changed=changed), self.assertRaises(
                    (ValueError, WholeBaselineError)):
                with patch('gate8_whole_native_baseline._original_sections', return_value=()):
                    _source_program(events, image, BASES[0], end, bss, asm,
                                    b'', b'', {POKE_RT: 'native-poke'}, changed)


if __name__ == '__main__':
    unittest.main()

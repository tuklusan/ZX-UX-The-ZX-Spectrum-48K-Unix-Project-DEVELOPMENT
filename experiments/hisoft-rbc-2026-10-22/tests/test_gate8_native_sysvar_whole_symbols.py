"""Original native PEEK/POKE source stays relocatable after full text changes."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from z80asm import asm
from z80mini import Z80
from native_sysvars_rt import _native_peek, _native_poke, BSS_BYTES
from spectrum_sysvars import FLAGS2


SYMBOLS = dict(entry_label='rbc_sysvar_runtime', bss_label='rbc_sysvar_storage',
               end_label='rbc_process_end', start_label='start')
BASES = (0x6000, 0x7000, 0x8000)


def native_pair(fn, prefix, tail, extra_bss, base, font_alias=None):
    length = len(fn(asm, 0, 0, font_alias=font_alias))
    bss = prefix + length + tail
    total = bss + BSS_BYTES + extra_bss
    raw, body = fn(asm, bss, base, total, font_alias, prefix,
                   whole_program_symbols=SYMBOLS)
    source = ('    section text\n    global start\nstart:\n' +
              '    nop\n' * prefix + body +
              ('    section data\n    db ' + ','.join('195' for _ in range(tail)) +
               '\n' if tail else '') +
              '    section bss\nrbc_sysvar_storage:\n' +
              f'    ds {BSS_BYTES}\n' +
              (f'    ds {extra_bss}\n' if extra_bss else '') +
              'rbc_process_end:\n')
    obj = ras.assemble_text(source, 'rbc-sysvar-symbolic.s')
    ssx, *_ = rld.link([rld.Obj(obj, 'rbc-sysvar-symbolic.sso')], [],
                       entry='start', stack=384)
    parsed = rld.parse_ssx(ssx)
    loaded = bytes(rld.relocate(parsed['image'], parsed['relocs'], base))
    assert parsed['entry'] == 0 and parsed['bss'] == BSS_BYTES + extra_bss
    assert loaded[prefix:prefix + length] == raw
    assert len(parsed['image']) == bss
    assert len(parsed['relocs']) >= 30
    return parsed, loaded, ssx, bss, total, source


class WholeProgramNativeSysvarSymbols(unittest.TestCase):
    def test_three_bases_and_changed_text_layout(self):
        for fn in (_native_peek, _native_poke):
            for prefix, tail, extra in ((0, 0, 0), (7, 5, 11), (23, 9, 31)):
                for base in BASES:
                    with self.subTest(fn=fn.__name__, prefix=prefix, base=base):
                        info, loaded, ssx, bss, total, source = native_pair(
                            fn, prefix, tail, extra, base)
                        self.assertIn('rbc_sysvar_storage', source)
                        self.assertIn('rbc_process_end-1', source)
                        self.assertIn('ld de,start', source)
                        self.assertNotIn('start+-', source)
                        self.assertEqual(info['size'], len(ssx))
                        self.assertLess(max(len(ssx), total+384), 14000)
                        if tail:
                            self.assertEqual(loaded[bss-tail:bss], bytes([195])*tail)

    def test_live_native_poke_uses_relocated_private_bss(self):
        for base in BASES:
            with self.subTest(base=base):
                prefix = 7
                info, loaded, _ssx, bss, _total, _source = native_pair(
                    _native_poke, prefix, 5, 11, base)
                mem = bytearray(65536)
                mem[base:base+len(loaded)] = loaded
                mem[FLAGS2] = 0x99
                cpu = Z80(mem)
                cpu.sp, cpu.hl, cpu.e = 0xe000, FLAGS2, 0x42
                cpu.call(base + prefix, sentinel=0xb000)
                self.assertEqual(mem[base+bss], 0x42)
                self.assertEqual(mem[FLAGS2], 0x99)
                self.assertEqual(cpu.sp, 0xe000)

    def test_legacy_bytes_and_fixed_source_stay_unchanged(self):
        for fn in (_native_peek, _native_poke):
            with self.subTest(fn=fn.__name__):
                plain = fn(asm, 0x300, 0x7000, 0x500, None, 0x80)
                binary, fixed, positions = fn(asm, 0x300, 0x7000, 0x500,
                                              None, 0x80, with_source=True)
                self.assertEqual(binary, plain)
                self.assertIn('start:', fixed)
                self.assertGreater(len(positions), 20)

    def test_untyped_or_ambiguous_anchor_rejected(self):
        for fn in (_native_peek, _native_poke):
            with self.subTest(fn=fn.__name__):
                for symbols, bss, total in ((dict(SYMBOLS, bss_label='start'), 500, 520),
                                            (dict(SYMBOLS, entry_label='1bad'), 500, 520),
                                            (SYMBOLS, 500, 513)):
                    with self.assertRaises(ValueError):
                        fn(asm, bss, 0x7000, total, None, 50,
                           whole_program_symbols=symbols)
                with self.assertRaises(ValueError):
                    fn(asm, 500, 0x7000, 520, None, 50, with_source=True,
                       whole_program_symbols=SYMBOLS)


if __name__ == '__main__':
    unittest.main()

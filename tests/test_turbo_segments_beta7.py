"""Independent structural/negative test for the boot-only segment envelope."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import struct
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'release/src/zx-ux-sdk/tools/turbo_segments.py'
spec = importlib.util.spec_from_file_location('turbo_segments', MODULE)
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)


class TurboPacketContract(unittest.TestCase):
    def setUp(self):
        self.image = bytes((i * 17 + 29) % 256 for i in range(25596))
        self.blocks = t.make_segments(self.image)

    def test_independent_crc_vector(self):
        self.assertEqual(t.crc16_ccitt_false(b'123456789'), 0x29b1)

    def test_splitting_and_reconstruction(self):
        self.assertEqual(len(self.blocks), 24)
        self.assertEqual(len(self.blocks[0]), 1067 + 11)
        self.assertEqual(len(self.blocks[-1]), 1066 + 11)
        self.assertEqual(t.read_segments(self.blocks, image_length=len(self.image)), self.image)
        self.assertEqual(sum(n for _, n in t.layout(len(self.image))), len(self.image))

    def test_xor_consistent_bad_crc(self):
        damaged = bytearray(self.blocks[11]); damaged[77] ^= 0x40
        damaged[-1] ^= 0x40
        with self.assertRaisesRegex(t.TurboFormatError, 'CRC'):
            t.read_packet(bytes(damaged), ordinal=12, offset=t.layout(len(self.image))[11][0], size=t.layout(len(self.image))[11][1])

    def test_wrong_index_even_when_crc_xor_correct(self):
        damaged = bytearray(self.blocks[11]); damaged[3] = 13
        body = bytes(damaged[:-3]); crc = t.crc16_ccitt_false(body)
        damaged[-3:-1] = struct.pack('<H', crc)
        damaged[-1] = t.xor_bytes(bytes(damaged[:-1]))
        with self.assertRaisesRegex(t.TurboFormatError, 'ordinal'):
            t.read_segments([*self.blocks[:11], bytes(damaged), *self.blocks[12:]], image_length=len(self.image))

    def test_bad_offsets_and_truncations(self):
        for candidate in [self.blocks[:23], self.blocks + self.blocks[:1],
                          [*self.blocks[:6], self.blocks[6][:-1], *self.blocks[7:]],
                          [*self.blocks[:6], self.blocks[7], self.blocks[6], *self.blocks[8:]]]:
            with self.assertRaises(t.TurboFormatError):
                t.read_segments(candidate, image_length=len(self.image))

    def test_cannot_reach_ce00_or_start_above_entry(self):
        for base in (0x6000, 0xB000, -1):
            with self.assertRaises(t.TurboFormatError):
                t.layout(25596, load_base=base)

    def test_turbo_record_timing(self):
        packet = self.blocks[0]
        record = t.pack_turbo_record(packet, pause_ms=400)
        self.assertEqual(record[0], 0x11)
        self.assertEqual(struct.unpack_from('<6H', record, 1), t.TIMINGS)
        self.assertEqual(record[13], 8)
        self.assertEqual(struct.unpack_from('<H', record, 14)[0], 400)
        self.assertEqual(int.from_bytes(record[16:19], 'little'), len(packet))
        self.assertEqual(record[19:], packet)

    def test_reject_noncanonical_magic_and_version(self):
        for which in (0, 2):
            altered = bytearray(self.blocks[0]); altered[which] ^= 1
            altered[-1] ^= 1
            with self.assertRaises(t.TurboFormatError):
                t.read_segments([bytes(altered), *self.blocks[1:]], image_length=len(self.image))


def independent_decode_tzx(tzx):
    """Read TZX records without calling production encoding/parsing helpers."""
    assert tzx[:10] == b'ZXTape!\x1a\x01\x14'
    cursor, forms, payloads = 10, [], []
    while cursor < len(tzx):
        form = tzx[cursor]
        if form == 0x10:
            pause, size = struct.unpack_from('<HH', tzx, cursor + 1)
            end = cursor + 5 + size
            block = tzx[cursor + 5:end]
            assert len(block) == size
            forms.append(form)
            payloads.append((pause, block))
        elif form == 0x11:
            speed = struct.unpack_from('<6H', tzx, cursor + 1)
            valid_bits = tzx[cursor + 13]
            pause = struct.unpack_from('<H', tzx, cursor + 14)[0]
            size = int.from_bytes(tzx[cursor + 16:cursor + 19], 'little')
            end = cursor + 19 + size
            block = tzx[cursor + 19:end]
            assert len(block) == size and valid_bits == 8
            assert speed == (2042, 875, 613, 513, 1025, 247)
            forms.append(form)
            payloads.append((pause, block))
        else:
            raise ValueError('unknown TZX record type')
        cursor = end
    assert cursor == len(tzx)
    return forms, payloads


class ActualLinkerImageContract(unittest.TestCase):
    def test_real_image_and_tzx_framing(self):
        import binascii
        root = Path(__file__).resolve().parents[1]
        image = root / 'release/build/out/merged-image.bin'
        standard_tap = root / 'release/build/out/ZX-UX.tap'
        if not image.exists() or not standard_tap.exists():
            self.skipTest('no fresh offline link output under release/build')
        data = image.read_bytes()
        raw = standard_tap.read_bytes()
        pairs = []
        position = 0
        while position < len(raw):
            width = int.from_bytes(raw[position:position+2], 'little')
            position += 2
            pairs.append(raw[position:position+width])
            position += width
        self.assertEqual(len(pairs), 4)
        self.assertEqual(pairs[-1][1:-1], data)
        packets = t.make_segments(data)
        rebuilt = bytearray()
        for number, packet in enumerate(packets, start=1):
            self.assertEqual(packet[:2], b'ZX')
            self.assertEqual(packet[3], number)
            offset, length = struct.unpack_from('<HH', packet, 4)
            self.assertEqual(offset, len(rebuilt))
            self.assertEqual(len(packet), length + 11)
            self.assertEqual(binascii.crc_hqx(packet[:-3], 0xffff), int.from_bytes(packet[-3:-1], 'little'))
            self.assertEqual(sum_of_xor(packet), 0)
            rebuilt.extend(packet[8:-3])
        self.assertEqual(bytes(rebuilt), data)
        # The second pair in the normal TAP is the *entire system image*,
        # not the compact D000 bootstrap! Reusing it here would duplicate
        # 25 KB and violate the strict size requirement.
        prototype = root / 'release/build/out/ZX-UX.tzx'
        if not prototype.exists():
            self.fail('fresh boot turbo TZX was not generated by offline builder')
        forms, prior = independent_decode_tzx(prototype.read_bytes())
        self.assertEqual(forms, [0x10]*4 + [0x11]*24)
        compact_boot_pair = [prior[2][1], prior[3][1]]
        with self.assertRaisesRegex(t.TurboFormatError, '30,000'):
            t.pack_tzx(pairs[:2], pairs[2:], data, pause_ms=400)
        tzx = t.pack_tzx([prior[0][1], prior[1][1]], compact_boot_pair, data, pause_ms=400)
        self.assertLess(len(tzx), 30_000)
        forms, blocks = independent_decode_tzx(tzx)
        self.assertEqual(forms, [0x10]*4 + [0x11]*24)
        self.assertEqual([item[1] for item in blocks[4:]], list(packets))
        self.assertEqual({pause for pause, _ in blocks[4:]}, {400})


def sum_of_xor(data):
    result = 0
    for part in data:
        result ^= part
    return result


if __name__ == '__main__':
    unittest.main()

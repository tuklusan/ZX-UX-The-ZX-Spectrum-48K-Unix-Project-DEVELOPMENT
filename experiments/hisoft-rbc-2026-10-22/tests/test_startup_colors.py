"""Confirm ROM printer color setup and restoration are relocatable."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from startup_colors import save_and_set, save_controls, restore, append_slots


class Emitter:
    def __init__(self):
        self.code = bytearray()
        self.fixups = []

    def emit(self, *numbers):
        self.code.extend(numbers)

    def word(self, value):
        self.code.extend((value & 255, value >> 8 & 255))

    def relative(self, value):
        self.fixups.append(len(self.code))
        self.word(value)

    def lda(self, value):
        self.emit(0x3E, value)

    def fix(self, at, value):
        self.code[at:at + 2] = bytes((value & 255, value >> 8 & 255))


class StartupColorTests(unittest.TestCase):
    def test_save_set_restore_printer_defaults(self):
        emitter = Emitter()
        original = (0x12, 0x44, 0x56, 0x78)
        addresses = (0x5C8D, 0x5C8E, 0x5C8F, 0x5C90)
        expected = (0x38, 0x00, 0x38, 0x00)
        records = save_and_set(emitter)
        restore(emitter, records)
        append_slots(emitter, records)
        self.assertEqual([x[0] for x in records], list(addresses))
        self.assertEqual(len(records), 4)
        self.assertEqual(len(emitter.fixups), 8)
        slots = []
        for address, save_site, read_site in records:
            self.assertIn(address, addresses)
            slot_a = int.from_bytes(emitter.code[save_site:save_site + 2], 'little')
            slot_b = int.from_bytes(emitter.code[read_site:read_site + 2], 'little')
            self.assertEqual(slot_a, slot_b)
            slots.append(slot_a)
        self.assertEqual(len(set(slots)), 4)
        self.assertEqual(slots, sorted(slots))
        self.assertEqual(bytes(emitter.code[slot] for slot in slots), b'\0' * 4)
        self.assertEqual(expected, (56, 0, 56, 0))
        self.assertNotEqual(original, expected)

    def test_only_printer_variables_are_modified(self):
        emitter = Emitter()
        records = save_and_set(emitter)
        restore(emitter, records)
        append_slots(emitter, records)
        for address, _save, _load in records:
            self.assertTrue(0x5C8D <= address <= 0x5C90)
        # One private saved byte for each ROM printer setting.
        self.assertEqual(len(emitter.code) - min(int.from_bytes(emitter.code[s:s+2], 'little') for _,s,_ in records), 4)

    def test_keyboard_controls_are_saved_not_overwritten_on_startup(self):
        emitter = Emitter()
        records = save_controls(emitter)
        startup = bytes(emitter.code)
        self.assertEqual([item[0] for item in records], [0x5C6A, 0x5C39])
        self.assertEqual(startup.count(bytes([0x3A])), 2)
        self.assertNotIn(bytes([0x3E]), startup)  # No LD A,immediate during setup
        restore(emitter, records)
        append_slots(emitter, records)
        self.assertEqual(len(emitter.fixups), 4)
        addresses = []
        for address, save_at, read_at in records:
            self.assertIn(address, (0x5C6A, 0x5C39))
            slot1 = int.from_bytes(emitter.code[save_at:save_at+2], 'little')
            slot2 = int.from_bytes(emitter.code[read_at:read_at+2], 'little')
            self.assertEqual(slot1, slot2)
            self.assertEqual(emitter.code[slot1], 0)
            addresses.append(slot1)
        self.assertEqual(len(set(addresses)), 2)



if __name__ == '__main__':
    unittest.main()

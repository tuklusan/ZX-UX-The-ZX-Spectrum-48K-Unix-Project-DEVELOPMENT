"""Exercise the original token safety boundary for external commands."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from external_io_policy import reject_external_commands, UnsupportedExternalIO

NAMES = {0xe0:'LPRINT',0xe1:'LLIST',0xcf:'CAT',0xd0:'FORMAT',
         0xd1:'MOVE',0xd2:'ERASE',0xd3:'OPEN #',0xd4:'CLOSE #'}


class ExternalIOTests(unittest.TestCase):
    def test_each_external_command_is_rejected(self):
        for code,name in NAMES.items():
            with self.subTest(name=name), self.assertRaisesRegex(
                    UnsupportedExternalIO, 'Line 20: '+name):
                reject_external_commands([(10,b'\xf5 "normal"'),(20,bytes([code]))],NAMES)

    def test_strings_and_comments_do_not_execute(self):
        reject_external_commands([(10,b'\xf5 "'+bytes(NAMES)+b'"'),
                                  (20,b'\xea '+bytes(NAMES))],NAMES)

    def test_data_field_is_not_executable(self):
        reject_external_commands([(10,b'\xe4 '+bytes(NAMES)+b',"a:b"')],NAMES)
        with self.assertRaisesRegex(UnsupportedExternalIO,'Line 10: LLIST'):
            reject_external_commands([(10,b'\xe4 "a:b":\xe1')],NAMES)

    def test_numeric_metadata_is_ignored(self):
        reject_external_commands([(10,b'\xf5 12\x0e'+bytes([0xe0,0xe1,0xcf,0xd0,0xd1])+b'\r')],NAMES)

    def test_missing_printer_tokens_fails_closed(self):
        with self.assertRaises(UnsupportedExternalIO):
            reject_external_commands([(10,b'\xe0')],{})

if __name__=='__main__':
    unittest.main()

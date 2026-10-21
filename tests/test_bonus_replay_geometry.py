#!/usr/bin/env python3
"""Ensure visual review never passes merely because both screens have blue paper."""
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from bonus_replay import geometry


class SpectrumGeometry(unittest.TestCase):
    def test_matching_foreground(self):
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/'a.png';b=Path(temp)/'b.png'
            for p in [a,b]:
                im=Image.new('RGB',(320,240),(0,0,197))
                ImageDraw.Draw(im).rectangle((80,48,231,55),fill=(197,197,0))
                im.save(p)
            self.assertEqual(geometry(a,b,[80,48,232,176],.99),1.0)

    def test_blue_background_is_not_a_false_match(self):
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/'a.png';b=Path(temp)/'b.png'
            for p,x in [(a,80),(b,200)]:
                im=Image.new('RGB',(320,240),(0,0,197))
                ImageDraw.Draw(im).rectangle((x,48,x+10,60),fill=(197,197,0))
                im.save(p)
            with self.assertRaisesRegex(AssertionError,'pixel mismatch'):
                geometry(a,b,[80,48,232,176],.2)

    def test_real_native_oxo_board_colors(self):
        root=ROOT/'release/dist/bonus/60-programs/29-oxo'
        pairs=(('01-INTRO.png','01-intro.png'),
               ('02-MAIN.png','02-main.png'),
               ('03-AFTER-INPUT.png','04-result.png'))
        for ref,capture in pairs:
            a=root/'BASIC/SCREENSHOTS'/ref
            b=root/'C48/screenshots/fuse'/capture
            if not b.is_file():self.skipTest('actual Fuse capture not present')
            original=Image.open(a).convert('RGB').crop((80,48,232,176))
            native=Image.open(b).convert('RGB').crop((80,48,232,176))
            same=sum(a==b for a,b in zip(original.get_flattened_data(),
                                         native.get_flattened_data()))
            self.assertGreater(same/(152*128),.97,(ref,capture,same))

    def test_real_oxo_original_vs_port(self):
        root=ROOT/'release/dist/bonus/60-programs/29-oxo'
        ref=root/'BASIC/SCREENSHOTS/01-INTRO.png'
        image=root/'C48/screenshots/rvm/01-intro.png'
        if not image.is_file():self.skipTest('actual RVM capture not present')
        self.assertGreater(geometry(ref,image,[80,48,232,176],.95),.97)


if __name__=='__main__':
    unittest.main()

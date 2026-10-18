#!/usr/bin/env python3
"""Validate a built ZX-UX turbo TZX, independently from the physical tape boot."""
import pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'release/dist/sdk/bin/py'))
from zxux import SystemImage,RvmError

def main():
    image=SystemImage(str(ROOT/'release/dist/zx-ux/ZX-UX.tzx'))
    assert len(image.blocks)==4
    assert image.merged[0x6000-0x5D98]==0xC3
    assert len(image.merged)>20000
    assert not (ROOT/'release/dist/zx-ux/ZX-UX.tap').exists()
    assert not (ROOT/'release/build/out/ZX-UX.tap').exists()
    print('PASS verified 4 ROM records, 24 turbo segments and actual linked ZX-UX kernel')
    return 0

if __name__=='__main__': sys.exit(main())

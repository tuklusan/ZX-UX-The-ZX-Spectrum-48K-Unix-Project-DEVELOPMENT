#!/usr/bin/env python3
"""Prove that native C48 recursive frame entry and exit preserve IX and SP.

The test uses current SSO1 objects, current ZX-UX frame.asm, and a Z80
simulator. It makes no claim about other registers or every call type.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'sdk'))
import ras
import rld
from skoolkit import CSimulator
from skoolkit.simutils import A, HALT, IXh, IXl, SP


def run():
    frame_file = ROOT / 'sdk/lib/frame.asm'
    frame = frame_file.read_bytes()
    frame_object = rld.Obj(ras.assemble_text(frame.decode('ascii'),
                                             'frame.asm'), 'frame.asm')
    cases = []
    for ix in (0, 1, 0xA55A, 0xFFFF):
        for stack in (0xE000, 0xF000):
            source = '''
 section text
 global start,@noret
 extern @enter,@leave0
start:  di
        ld sp,%d
        ld ix,%d
        call outer
        ld hl,%d
        push ix
        pop de
        or a
        sbc hl,de
        jp nz,failed
        ld a,1
        halt
failed: xor a
        halt
outer:  call @enter
        dw 2
        call inner
        jp @leave0
inner:  call @enter
        dw 4
        ld hl,0x1234
        jp @leave0
@noret: xor a
        halt
''' % (stack, ix, ix)
            obj = rld.Obj(ras.assemble_text(source, 'ix-witness.asm'),
                          'ix-witness.asm')
            image, _bss, entry, _symbols, _chosen = rld.link(
                [obj, frame_object], [], org=0x8000)
            memory = [0] * 65536
            memory[0x8000:0x8000 + len(image)] = image
            sim = CSimulator(memory, registers={'PC': 0x8000 + entry})
            for step in range(300):
                sim.run()
                if sim.registers[HALT]:
                    break
            else:
                raise AssertionError('witness did not halt')
            observed = sim.registers[IXh] * 256 + sim.registers[IXl]
            assert (sim.registers[A], observed, sim.registers[SP]) == (
                1, ix, stack), 'IX or SP changed across nested frames'
            cases.append({'ix': ix, 'stack': stack, 'steps': step + 1,
                          'image_sha256': hashlib.sha256(image).hexdigest()})
    return {'name': 'native_ix_register_preservation_8_cases',
            'frame_sha256': hashlib.sha256(frame).hexdigest(),
            'result': 'PASS', 'count': len(cases), 'cases': cases}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = run()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: %d direct IX preservation witnesses' % result['count'])


if __name__ == '__main__':
    main()

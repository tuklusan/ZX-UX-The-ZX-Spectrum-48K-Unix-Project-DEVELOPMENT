#!/usr/bin/env python3
"""Record the ZX-UX 48K loader's rejection of an oversized LM image.

This diagnostic does not execute the LM program and is not release proof.
The caller must independently establish a fresh tape-derived snapshot.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tools'), str(ROOT / 'sdk')]
import rld  # noqa: E402
import rtap  # noqa: E402
import rvm  # noqa: E402
import suite  # noqa: E402
import zxrun  # noqa: E402

ROM_SHA256 = 'd55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42'
MESSAGE = '/dev/cassette/ailmzx48: not enough memory'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observe(snapshot, ssx, tape, output, frames=4000):
    rom = ROOT / 'rom/48.rom'
    source = ROOT / 'programs/c48/ailmzx48/ailmzx48.c'
    required = (rom, snapshot, ssx, tape, source)
    if any(not path.is_file() or path.is_symlink() for path in required):
        raise RuntimeError('required source, ROM, tape, snapshot or image missing')
    if digest(rom) != ROM_SHA256:
        raise RuntimeError('unexpected Spectrum 48K ROM')
    binary = ssx.read_bytes()
    if binary[:4] != b'SSX1':
        raise RuntimeError('LM is not in the native SSX1 format')
    image = rld.parse_ssx(binary)
    if image['flags'] != 0:
        raise RuntimeError('LM is not a native program')
    needed = rtap.need(binary)
    session = suite.Session(str(snapshot))
    session.login()
    free_before = suite.df_free(session)
    if needed <= free_before:
        raise RuntimeError('LM fits available RAM; memory refusal is not the expected outcome')
    session.zx.type('/dev/cassette/ailmzx48\n')
    session.zx.tr.edges = zxrun.tape_pulses(
        rtap.records(binary, 'ailmzx48'),
        session.zx.sim.registers[25] + 350000)
    observed = None
    for frame in range(frames):
        session.zx.run(1)
        if frame % 2 == 0 and MESSAGE in session.screen():
            observed = frame + 1
            break
    if observed is None or session.screen().count(MESSAGE) != 1:
        raise RuntimeError('native LM memory rejection not observed')
    pixels = bytes(session.zx.mem[0x4000:0x5b00])
    if len(pixels) != 6912:
        raise RuntimeError('Spectrum screen capture truncated')
    if output.is_symlink():
        raise RuntimeError('capture directory must not be a symbolic link')
    output.mkdir(parents=True, exist_ok=True)
    scr = output / 'lm-rejected.scr'
    png = output / 'lm-rejected.png'
    if scr.is_symlink() or png.is_symlink():
        raise RuntimeError('capture files must not be symbolic links')
    scr.write_bytes(pixels)
    rvm.write_png(pixels, str(png), session.zx.tr.border)
    free_after = suite.df_free(session)
    if free_after < free_before - 8:
        raise RuntimeError('memory not reclaimed after the rejected load')
    result = {'result': 'PASS_MEMORY_BOUND_REJECTION',
              'scope': 'loader rejection only; LM program was not executed',
              'frame': observed, 'image_bytes': len(binary),
              'required_bytes': needed,
              'kernel_free_before': free_before, 'kernel_free_after': free_after,
              'sha256': {name: digest(path) for name, path in {
                  'source': source, 'rom': rom, 'tape': tape,
                  'snapshot': snapshot, 'native_image': ssx,
                  'screen': scr, 'png': png}.items()}}
    (output / 'lm-native-memory.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', type=Path, default=ROOT / 'build/test.z80')
    parser.add_argument('--image', type=Path, default=ROOT / 'build/lm/ailmzx48.ssx')
    parser.add_argument('--tape', type=Path, default=ROOT / 'build/ZX-UX.tzx')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/logs/lm-native')
    args = parser.parse_args()
    try:
        print(json.dumps(observe(args.snapshot, args.image, args.tape, args.output), indent=2))
        return 0
    except (RuntimeError, OSError, ValueError) as error:
        print('LM diagnostic failed:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

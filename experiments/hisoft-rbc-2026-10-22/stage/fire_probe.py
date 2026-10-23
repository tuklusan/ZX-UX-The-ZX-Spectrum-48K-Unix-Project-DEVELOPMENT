#!/usr/bin/env python3
"""Check native Galaxians laser and scoring against an unfired control."""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path


def beam_pixels(bitmap: bytes, x=143):
    """Count lit pixels in the expected vertical laser column."""
    if len(bitmap) != 6912:
        raise ValueError('expected 6912-byte Spectrum screen')
    return sum(bool(bitmap[((y & 192) << 5) | ((y & 7) << 8) |
                           ((y & 56) << 2) | (x // 8)] & (128 >> (x % 8)))
               for y in range(40, 180))


def displayed_score(text):
    match = re.match(r'^SCORE:(\d+)', text)
    return int(match.group(1)) if match else 0


def run(root, binary, font, fire, output):
    import rvm
    import zxux
    opts = rvm.Options()
    opts.prog = str(binary)
    opts.system = str(root / 'dist/zx-ux/tzx/ZX-UX.tzx')
    opts.headless = True
    runner = rvm.Runner(opts)
    runner.start()
    for _ in range(9000):
        runner.frame()
        if runner.fg is not None and runner.fg.started is not None:
            break
    else:
        raise AssertionError('Galaxians did not boot')
    if runner.session.m.ula_issue != 2:
        raise AssertionError('expected ZX-UX native Issue 2 default')
    for _ in range(70):
        runner.frame()
    runner.session.kb.add([('press', zxux.char_keys(' '), 30)])
    for _ in range(100):
        runner.frame()
    if fire:
        runner.session.kb.add([('press', zxux.char_keys('m'), 110)])
    maximum = 0
    laser_frames = 0
    score = 0
    saved_beam = False
    from frame_probe import screen_letters
    for _ in range(150):
        runner.frame()
        screen, border = runner.picture()
        pixels = beam_pixels(screen)
        maximum = max(maximum, pixels)
        laser_frames += int(pixels >= 130)
        if fire and pixels >= 130 and not saved_beam:
            rvm.write_png(screen, str(output / 'galaxians-fire-beam.png'), border)
            saved_beam = True
        score = max(score, displayed_score(screen_letters(screen, font)[0]))
    return {'fire_held': fire, 'max_beam_pixels': maximum,
            'full_laser_frames': laser_frames, 'maximum_score': score,
            'ula_issue': runner.session.m.ula_issue}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--binary', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    root, binary, output = args.root.resolve(), args.binary.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root / 'dist/sdk/bin/py'))
    with zipfile.ZipFile(root / 'experiments/hisoft-rbc-2026-10-22/rbc-sinclair-font-checkpoint-2026-10-22.zip') as zf:
        font = zf.read('rbc/font32.bin')
    control = run(root, binary, font, False, output)
    fired = run(root, binary, font, True, output)
    result = {'control': control, 'held_fire': fired}
    (output / 'galaxians-fire-check.json').write_text(json.dumps(result, indent=2) + '\n')
    if not (control['max_beam_pixels'] < 30 and
            fired['max_beam_pixels'] >= 130 and fired['full_laser_frames'] > 0 and
            fired['maximum_score'] > control['maximum_score']):
        raise AssertionError('native Galaxians fire, laser, or score regression')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()

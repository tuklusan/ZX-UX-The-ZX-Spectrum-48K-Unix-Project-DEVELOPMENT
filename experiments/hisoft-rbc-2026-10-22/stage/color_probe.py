#!/usr/bin/env python3
"""Check native Sinclair BASIC color attributes against the original game."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def capture(root: Path, binary: Path, out: Path):
    sys.path.insert(0, str(root / 'dist/sdk/bin/py'))
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
        raise AssertionError('native BASIC program did not start')
    for _ in range(70):
        runner.frame()
    runner.session.kb.add([('press', zxux.char_keys(' '), 24)])
    for _ in range(75):
        runner.frame()
    bitmap, border = runner.picture()
    attrs = Counter(bitmap[6144:])
    if len(bitmap) != 6912:
        raise AssertionError('invalid native Spectrum screen')
    # The preserved original has black INK 0 on cyan PAPER 5 and
    # magenta INK 3 for defenses. White ink is not correct for enemies.
    black_on_cyan = attrs[0x28]
    magenta_on_cyan = attrs[0x2B]
    white_on_cyan = attrs[0x2F]
    result = {'game': binary.name, 'ula_issue': runner.session.m.ula_issue,
              'black_on_cyan_cells': black_on_cyan,
              'magenta_on_cyan_cells': magenta_on_cyan,
              'white_on_cyan_cells': white_on_cyan,
              'native_process_status': runner.fg.status}
    out.mkdir(parents=True, exist_ok=True)
    rvm.write_png(bitmap, str(out / 'invaders-color-check.png'), border)
    (out / 'invaders-color-check.json').write_text(json.dumps(result, indent=2) + '\n')
    if runner.session.m.ula_issue != 2:
        raise AssertionError('expected default Issue 2 ULA')
    if black_on_cyan < 600 or magenta_on_cyan < 16 or white_on_cyan:
        raise AssertionError('Invaders native INK/PAPER color mismatch')
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--binary', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(capture(args.root.resolve(), args.binary.resolve(),
                             args.output.resolve()), sort_keys=True))


if __name__ == '__main__':
    main()

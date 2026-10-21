#!/usr/bin/env python3
"""Replay a BASIC-to-C48 scenario on the actual ZX-UX kernel in RVM/FUSE.

Each port owns a small C48/SCENARIOS.json with actions, assertions and capture
names. Frames are saved as seen by the emulator, never rendered from a model.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'release/dist/bonus/60-programs'
SDK = ROOT / 'release/dist/sdk/bin/py'
sys.path.insert(0, str(SDK))


def scenario(program, name):
    if not program[:2].isdigit() or '/' in program:
        raise ValueError('invalid program')
    folder = BASE / program
    data = json.loads((folder / 'C48/SCENARIOS.json').read_text())
    case = next((c for c in data['cases'] if c['name'] == name), None)
    if case is None:
        raise ValueError('unknown case: ' + name)
    return folder, data['alias'], case


def run_rvm(folder, alias, case):
    import rvm
    import zxux
    import zxscreen
    binary = folder / 'C48/bin/ssx' / (alias + '.ssx')
    tape = folder / 'C48/bin/tzx' / (alias + '.tzx')
    import rtap
    actual = [record[1] for record in rtap.tzx_blocks(tape.read_bytes())[1]]
    if actual != rtap.records(binary.read_bytes(), alias):
        raise AssertionError('TZX does not contain the matching SSX')
    options = rvm.Options()
    options.prog = str(binary)
    options.headless = True
    runner = rvm.Runner(options)
    actions = zxux.parse_keys(case.get('keys', ''))
    for step in case.get('actions', []):
        if 'wait' in step:
            actions.append(('wait', int(step['wait'])))
        elif 'hold' in step:
            actions.append(('press', zxux.char_keys(step['hold']), int(step['scans'])))
        elif 'type' in step:
            actions.extend(zxux.parse_keys(step['type']))
        else:
            raise ValueError('unknown action')
    runner.keys = actions
    runner.start()
    why = None
    for frame in range(case.get('frames', 1100) + 300):
        runner.frame()
        why = runner.check(limit=case.get('frames', 1100))
        if why:
            break
    if runner.fg.started is None or why not in ('exit', 'input', 'frames'):
        raise AssertionError(f'ZX-UX did not run {alias}: {why}')
    scr, border = runner.picture()
    text = zxscreen.screen_text(scr)
    for expected in case.get('expect', []):
        if expected not in text:
            raise AssertionError(f'missing {expected!r} in {case["name"]}:\n{text}')
    for forbidden in case.get('forbid', []):
        if forbidden in text:
            raise AssertionError(f'forbidden {forbidden!r} in {case["name"]}:\n{text}')
    if 'capture' in case:
        output = folder / 'C48/screenshots/rvm' / case['capture']
        output.parent.mkdir(parents=True, exist_ok=True)
        rows = zxscreen.rgb_rows(scr, [border] * zxscreen.H)
        output.write_bytes(zxscreen.png_bytes(rows))
        print('RVM', alias, case['name'], why, output.relative_to(ROOT))
    else:
        print('RVM', alias, case['name'], why)
    return text


def run_fuse(folder, alias, case, args):
    sys.path.insert(0, str(ROOT / 'tools'))
    import fuse_portfolio
    import types
    fuse_portfolio.BIN = folder / 'C48/bin/ssx'
    namespace = types.SimpleNamespace(
        display=args.display, fuse=Path(args.fuse).resolve(),
        assets=Path(args.assets).resolve(),
        rom=(ROOT / 'release/src/zx-ux/rom/48.rom').resolve(),
        libdir=Path(args.libdir).resolve() if args.libdir else None,
        speed=args.speed, boot_wait=70, wait=3, multitask_wait=3)
    steps = case.get('fuse_steps', [])
    cfg = dict(post_command_wait=.2,
               capture_delay=float(case.get("fuse_capture_delay", .2)),
               fuse_wait=float(case.get("fuse_wait", 2.0)),
               sample_step=.2,
               input_key_pause=float(case.get("fuse_key_pause", .05)),
               input_steps=steps,
               prefer_color=bool(case.get("fuse_prefer_color", False)))
    output = folder / 'C48/screenshots/fuse' / case['capture']
    fuse_portfolio.run_case((alias,), output, namespace, cfg)
    # Assertions use the untouched emulator capture. The inner display is
    # inspected, never painted, and no "best looking" state is accepted if
    # its mandatory pixels are missing.
    if case.get('fuse_pixels'):
        from PIL import Image
        image = Image.open(output).convert('RGB')
        if image.size != (320, 240):
            raise AssertionError('native capture is not a full Spectrum display')
        for assertion in case['fuse_pixels']:
            left, top, right, bottom = assertion['box']
            if not (0 <= left < right <= 320 and 0 <= top < bottom <= 240):
                raise ValueError('invalid native image test region')
            pixels = image.crop((left, top, right, bottom)).getdata()
            lit = sum(min(rgb) > int(assertion.get('brightness', 100)) for rgb in pixels)
            if lit < int(assertion['min']) or lit > int(assertion['max']):
                raise AssertionError(
                    f'native state mismatch in {case["name"]}: '
                    f'{lit} lit pixels in {assertion["box"]}, '
                    f'expected {assertion["min"]}..{assertion["max"]}')
        print('Fuse state checked:', alias, case['name'])
    return output


def geometry(original, candidate, box, minimum):
    from PIL import Image
    from PIL import ImageChops
    a = Image.open(original).convert('RGB')
    b = Image.open(candidate).convert('RGB')
    if a.size != (320, 240) or b.size != (320, 240):
        raise AssertionError('expected 320x240 genuine Spectrum display')
    ap = a.crop(tuple(box)).getdata()
    bp = b.crop(tuple(box)).getdata()
    p = [max(v) > 95 for v in ap]
    q = [max(v) > 95 for v in bp]
    intersection = sum(x and y for x, y in zip(p, q))
    union = sum(x or y for x, y in zip(p, q))
    if not union or intersection / union < minimum:
        raise AssertionError(f'pixel mismatch: {intersection}/{union} (< {minimum})')
    return intersection / union


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--program', required=True)
    p.add_argument('--case', default='all')
    p.add_argument('--host', choices=['rvm', 'fuse'], default='rvm')
    p.add_argument('--fuse', default='/usr/bin/fuse-sdl')
    p.add_argument('--assets', default='/usr/share/fuse')
    p.add_argument('--libdir', default='')
    p.add_argument('--display', type=int, default=180)
    p.add_argument('--speed', type=int, default=100)
    args = p.parse_args()
    folder = BASE / args.program
    data = json.loads((folder / 'C48/SCENARIOS.json').read_text())
    cases = data['cases'] if args.case == 'all' else [scenario(args.program, args.case)[2]]
    for case in cases:
        if args.host == 'rvm':
            run_rvm(folder, data['alias'], case)
        elif 'capture' in case and 'fuse_steps' in case:
            run_fuse(folder, data['alias'], case, args)
    for check in data.get('geometry', []):
        candidate = folder / 'C48/screenshots' / args.host / check['capture']
        if candidate.is_file():
            ref = folder / 'BASIC/SCREENSHOTS' / check['reference']
            score = geometry(ref, candidate, check['box'], check['threshold'])
            print(args.host, check['capture'], f'pixel-overlap={score:.3f}')


if __name__ == '__main__':
    main()

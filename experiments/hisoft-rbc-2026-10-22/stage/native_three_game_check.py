"""Repeat native game input and embedded font tests on real ZX-UX software.

This script consumes separately linked trial SSX files. It never changes a
historical BASIC file, a linked executable, or the frozen system tape.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import rld
import rvm
import zxux


def digest(data):
    return hashlib.sha256(data).hexdigest()


def start(path, kernel):
    opts = rvm.Options()
    opts.prog = str(path)
    opts.system = str(kernel)
    opts.headless = True
    vm = rvm.Runner(opts)
    vm.start()
    for _ in range(9000):
        vm.frame()
        if vm.fg and vm.fg.started is not None:
            return vm
    raise AssertionError(f'Native ZX-UX process did not start: {path.name}')


def tick(vm, frames):
    for _ in range(frames):
        vm.frame()
    return vm.picture()[0]


def check_bricklayer(path, kernel):
    still = start(path, kernel)
    tick(still, 90)
    before = digest(still.picture()[0])
    after = digest(tick(still, 180))
    if after != before:
        raise AssertionError('PAUSE 0 changed the screen without keyboard input')
    active = start(path, kernel)
    tick(active, 90)
    first = digest(active.picture()[0])
    active.session.kb.add([('press', zxux.char_keys('x'), 25)])
    final = digest(tick(active, 180))
    if first != before or first == final or active.fg.ended is not None:
        raise AssertionError('PAUSE 0 failed to respond to a native key press')
    return {'stable_without_key': True, 'key_advances': True,
            'pre_key_image': first, 'post_key_image': final}


def check_font(path, kernel, font):
    ssx = rld.parse_ssx(path.read_bytes())
    bank = bytes(256) + font
    if len(font) != 768 or bank not in ssx['image']:
        raise AssertionError('Expected private VGA font is absent from linked image')
    vm = start(path, kernel)
    tick(vm, 200)
    memory = vm.session.m.mem
    pointer = memory[0x5c36] + (memory[0x5c37] << 8)
    if bytes(memory[pointer:pointer+1024]) != bank:
        raise AssertionError('Live CHARS does not point at the embedded private font')
    return {'bank_in_image': True, 'live_chars_matches': True,
            'font_sha256': digest(font), 'font_pointer': pointer}


def check_dogfight(path, kernel):
    vm = start(path, kernel)
    tick(vm, 130)
    intro = digest(vm.picture()[0])
    vm.session.kb.add([('press', zxux.char_keys('x'), 25)])
    bad = []
    def at_check(machine):
        if machine.cpu.b > 21 or bool(machine.cpu._f & 1):
            bad.append({'row': machine.cpu.b, 'column': machine.cpu.c,
                        'rom_pc': machine.cpu.pc})
        return False
    vm.session.m.hooks[0x0aac] = at_check
    for frame in range(1500):
        vm.frame()
        if bad or vm.fg.ended is not None:
            break
    later = digest(vm.picture()[0])
    return {'intro_screen': intro, 'later_screen': later,
            'scene_advanced': intro != later,
            'first_invalid_rom_at': bad[0] if bad else None,
            'ended': vm.fg.ended is not None,
            'gameover_and_restart_verified': False}


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--bin-dir', type=Path, required=True)
    args.add_argument('--system', type=Path, required=True)
    args.add_argument('--font', type=Path, required=True)
    ns = args.parse_args()
    images = {}
    for game in ('42-bricklayer', '43-dogfight', '53-russian-roulette'):
        path = ns.bin_dir / (game + '.ssx')
        if not path.is_file():
            raise RuntimeError('Native game output missing: ' + game)
        data = path.read_bytes()
        obj = rld.parse_ssx(data)
        total = len(obj['image']) + obj['bss'] + obj['stack']
        if max(len(data), total) > 12000:
            raise RuntimeError(game + ' exceeds the normal loader memory limit')
        images[game] = {'file': len(data), 'image': len(obj['image']),
                        'bss': obj['bss'], 'stack': obj['stack'],
                        'total': total, 'sha256': digest(data)}
    if not ns.system.with_name('kernel.json').exists():
        raise RuntimeError('Native kernel metadata is missing')
    if ns.system.read_bytes() != (ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise RuntimeError('Native boot tape differs from frozen release')
    images['42-bricklayer']['runtime'] = check_bricklayer(ns.bin_dir/'42-bricklayer.ssx', ns.system)
    images['53-russian-roulette']['runtime'] = check_font(ns.bin_dir/'53-russian-roulette.ssx', ns.system, ns.font.read_bytes())
    images['43-dogfight']['runtime'] = check_dogfight(ns.bin_dir/'43-dogfight.ssx', ns.system)
    print(json.dumps(images, indent=2), flush=True)
    if not images['43-dogfight']['runtime']['scene_advanced']:
        raise AssertionError('Dogfight did not start its game after native keyboard input')
    if images['43-dogfight']['runtime']['first_invalid_rom_at'] is not None:
        print('Dogfight reached an invalid ROM PRINT AT coordinate; game-over restart is NOT verified', file=sys.stderr)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Capture real Fuse ZX Spectrum 48K screenshots of a freshly built C48 set.

Each capture boots the unmodified ZX-UX TZX and loads the selected SSX
via the kernel's /dev/cassette path. No simulated system calls or image
substitutions. Xvfb, Fuse SDL and Pillow must be installed externally.
"""
import argparse
import concurrent.futures
import ctypes
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from html import escape
from urllib.parse import quote
from PIL import ImageGrab, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'release/dist/sdk/bin/py'), str(ROOT / 'tools')]
from fuse_boot import (SCREEN_WIDTH, SCREEN_HEIGHT, SPECTRUM_X, SPECTRUM_Y,
                       zxux_login_match, send_rom_load)
from gallery import write_gallery
from portfolio import captures, BIN, DIST, PAIRS, SOURCES
import rtap

OUT = DIST / 'screenshots/fuse'

# Surgical Fuse-only overrides for screenshots that were being caught on
# their greyed exit screens or with the wrong timing. The rest of the
# release gallery stays on the established behaviour.
FUSE_CAPTURE = {
    'dizzy4k': {'args': ['24'], 'post_command_wait': .2, 'capture_delay': 4.5,
                'fuse_wait': .7, 'sample_step': .10, 'prefer_color': True,
                'fuse_speed': 300},
    'firework': {'args': [], 'post_command_wait': .2, 'capture_delay': .2,
                 'fuse_wait': 6.0, 'sample_step': .10, 'prefer_color': True},
    'plasma': {'args': [], 'post_command_wait': .2, 'capture_delay': .2,
               'fuse_wait': 4.0, 'sample_step': .10, 'prefer_color': True},
    'sprites': {'args': [], 'post_command_wait': .2, 'capture_delay': .2,
                'fuse_wait': 5.0, 'sample_step': .10, 'prefer_color': True},
    'tunnel': {'args': [], 'post_command_wait': .2, 'capture_delay': .2,
               'fuse_wait': 4.0, 'sample_step': .10, 'prefer_color': True},
    'warp': {'args': [], 'post_command_wait': .2, 'capture_delay': .2,
             'fuse_wait': 5.0, 'sample_step': .10, 'prefer_color': True},
    'argv': {'post_command_wait': .0, 'capture_delay': .0,
             'fuse_wait': .7, 'sample_step': .05, 'prefer_color': True,
             'fuse_speed': 300},
    'colors': {'post_command_wait': .0, 'capture_delay': .0,
               'fuse_wait': 4.0, 'sample_step': .05, 'prefer_color': True,
               'fuse_speed': 100, 'enter_pause': .20},
}


class Keyboard:
    """Send actual X11 key events to the running Fuse SDL window."""
    def __init__(self, display):
        self.x = ctypes.CDLL('libX11.so.6')
        self.t = ctypes.CDLL('libXtst.so.6')
        self.x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x.XOpenDisplay.restype = ctypes.c_void_p
        self.x.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.x.XFlush.argtypes = [ctypes.c_void_p]
        self.x.XSetInputFocus.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        self.x.XStringToKeysym.argtypes = [ctypes.c_char_p]
        self.x.XStringToKeysym.restype = ctypes.c_ulong
        self.x.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.x.XKeysymToKeycode.restype = ctypes.c_uint
        self.t.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
        self.ptr = self.x.XOpenDisplay(display.encode())
        if not self.ptr:
            raise RuntimeError('cannot open X display')
        info = subprocess.run(['xwininfo', '-root', '-tree'], env=dict(os.environ, DISPLAY=display),
                              capture_output=True, text=True, check=True).stdout
        windows = re.findall(r'^\s*(0x[0-9a-f]+)\s+"(Fuse[^"\n]*)"', info, re.M)
        if not windows:
            self.close()
            raise RuntimeError('Fuse window not present')
        self.x.XSetInputFocus(self.ptr, int(windows[0][0], 16), 1, 0)
        self.x.XFlush(self.ptr)

    def key(self, symbol, pause=.20):
        names = {'\n': 'Return', '\b': 'BackSpace', ' ': 'space', '/': 'slash', '&': 'ampersand'}
        name = names.get(symbol, symbol)
        # Fuse maps Control to Spectrum Symbol Shift. On the Spectrum,
        # Symbol Shift + 6 types '&'; host Shift + 7 does not.
        if name == 'ampersand':
            self.event('Control_L', True)
            self.event('6', True)
            time.sleep(pause)
            self.event('6', False)
            self.event('Control_L', False)
            time.sleep(pause)
            return
        shifted = symbol.isupper()
        if shifted:
            self.event('Shift_L', True)
        key_name = name if name in ('Return', 'BackSpace') else name.lower()
        self.event(key_name, True)
        time.sleep(pause)
        self.event(key_name, False)
        if shifted:
            self.event('Shift_L', False)
        time.sleep(pause)

    def event(self, name, down):
        keysym = self.x.XStringToKeysym(name.encode())
        keycode = self.x.XKeysymToKeycode(self.ptr, keysym)
        if not keycode:
            raise RuntimeError('X11 unmapped key: ' + name)
        self.t.XTestFakeKeyEvent(self.ptr, keycode, int(down), 0)
        self.x.XFlush(self.ptr)

    def type(self, value):
        for ch in value:
            self.key(ch)

    def close(self):
        if self.ptr:
            self.x.XCloseDisplay(self.ptr)
            self.ptr = None


def screenshot(display):
    image = ImageGrab.grab(xdisplay=display)
    # Crop to actual Fuse-rendered Spectrum display and border; never paint pixels.
    return image.crop((SPECTRUM_X - 32, SPECTRUM_Y - 24,
                       SPECTRUM_X + 288, SPECTRUM_Y + 216))


def run_case(names, destination, args, config=None):
    config = config or {}
    with tempfile.TemporaryDirectory(prefix='zxux-fuse-') as tmp:
        tape = Path(tmp) / 'run.tzx'
        inputs = [str(BIN / (name + '.ssx')) for name in names]
        if any(not Path(f).is_file() for f in inputs):
            raise RuntimeError('compiled program missing')
        if rtap.main(['-o', str(tape), '--after', str(DIST / 'zx-ux/ZX-UX.tzx')] + inputs):
            raise RuntimeError('cannot append program to boot TZX')
        display = ':' + str(args.display)
        screen = ['Xvfb', display, '-screen', '0', f'{SCREEN_WIDTH}x{SCREEN_HEIGHT}x24', '-nolisten', 'tcp']
        env = dict(os.environ, DISPLAY=display, SDL_VIDEODRIVER='x11', SDL_AUDIODRIVER='dummy')
        if args.libdir:
            env['LD_LIBRARY_PATH'] = str(args.libdir)
        xvfb = fuse = None
        kb = None
        try:
            xvfb = subprocess.Popen(screen, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(.8)
            if xvfb.poll() is not None:
                raise RuntimeError('Xvfb could not start')
            command = [str(args.fuse), '--machine', '48', '--rom-48', str(args.rom),
                       '--no-sound', '--speed', str(config.get('fuse_speed', args.speed)),
                       '--tape', str(tape), '--auto-load']
            fuse = subprocess.Popen(command, env=env, cwd=args.assets,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2.0)
            if fuse.poll() is not None:
                raise RuntimeError('Fuse stopped during ZX-UX boot')
            send_rom_load(display)
            deadline = time.monotonic() + args.boot_wait
            login = None
            while time.monotonic() < deadline:
                if fuse.poll() is not None:
                    raise RuntimeError('Fuse stopped before ZX-UX login')
                time.sleep(.5)
                if zxux_login_match(ImageGrab.grab(xdisplay=display)):
                    login = screenshot(display)
                    break
            if login is None:
                raise RuntimeError('fresh ZX-UX TZX did not reach login')
            kb = Keyboard(display)
            kb.type('root')
            kb.key('\n', pause=.8)
            time.sleep(2)
            if not ImageChops.difference(screenshot(display).crop((10, 50, 310, 125)),
                                         login.crop((10, 50, 310, 125))).getbbox():
                raise RuntimeError('ZX-UX shell was not reached after login')
            for name in names:
                values = [] if len(names) > 1 or name == 'hanoi' else config.get('args', [])
                command = '/dev/cassette/' + name + ''.join(' ' + str(v) for v in values)
                kb.type(command + (' &' if len(names) > 1 else ''))
                kb.key('\n', pause=config.get('enter_pause', .8))
                time.sleep(config.get('post_command_wait', 2.0))
            if len(names) == 1 and names[0] == 'invaders':
                kb.key('m', pause=.5)  # leave the intro for real gameplay
            if len(names) == 1 and names[0] == '3dpaint':
                time.sleep(2)
                kb.type('q')
            # Reusable replay controls. Two values type text; three values
            # hold one actual Spectrum key across multiple emulator scans.
            reached_checkpoint = False
            stop_region = config.get('stop_when_ink')
            for step in config.get('input_steps', ()):
                if len(step) == 2:
                    delay, keys = step
                    time.sleep(float(delay))
                    for ch in keys:
                        kb.key(ch, pause=float(config.get('input_key_pause', .20)))
                elif len(step) == 3:
                    delay, key, duration = step
                    if len(key) != 1 or float(duration) <= 0:
                        raise ValueError('hold requires one key and positive seconds')
                    time.sleep(float(delay))
                    # Shift is part of an uppercase held key too: a held
                    # Spectrum letter differs from tapping lowercase.
                    shifted = key.isupper()
                    if shifted:
                        kb.event('Shift_L', True)
                    kb.event(key.lower(), True)
                    try:
                        time.sleep(float(duration))
                    finally:
                        kb.event(key.lower(), False)
                        if shifted:
                            kb.event('Shift_L', False)
                else:
                    raise ValueError('invalid input step')
                if stop_region:
                    # Inspect genuine Fuse pixels after each input. Stop before
                    # the next key can accidentally restart a finished game.
                    time.sleep(float(stop_region.get('settle', .8)))
                    candidate = screenshot(display).convert('RGB')
                    box = tuple(stop_region['box'])
                    if len(box) != 4 or not (0 <= box[0] < box[2] <= 320
                                                and 0 <= box[1] < box[3] <= 240):
                        raise ValueError('invalid native stop region')
                    bg = candidate.getpixel(tuple(stop_region.get('background_point', [278,105])))
                    count = sum(max(abs(px[i]-bg[i]) for i in range(3)) > 60
                                for px in candidate.crop(box).get_flattened_data())
                    if count >= int(stop_region['min']):
                        reached_checkpoint = True
                        print('Fuse input checkpoint reached:', names[0], count, flush=True)
                        break
            if stop_region and not reached_checkpoint:
                raise RuntimeError('native input checkpoint was never reached')
            # Real emulator timing; choose developed frames without filling the
            # gallery with the same boot/login screen.
            duration = args.multitask_wait if len(names) > 1 else float(config.get('fuse_wait', args.wait))
            sample_step = float(config.get('sample_step', 1.0))
            capture_delay = float(config.get('capture_delay', 0.0))
            if capture_delay > 0:
                time.sleep(capture_delay)
            loops = max(1, int(duration / sample_step + 0.999))
            best = None
            best_score = -1
            for _ in range(loops):
                time.sleep(sample_step)
                candidate = screenshot(display)
                changed = ImageChops.difference(candidate.convert('RGB'), login.convert('RGB'))
                bbox = changed.getbbox()
                if not bbox:
                    continue
                # Judge actual program pixels, not Fuse's coloured border.
                inner = candidate.crop((32, 24, 288, 216)).convert('L')
                score = sum(v > 48 for v in inner.resize((80, 60)).get_flattened_data())
                if config.get('prefer_color'):
                    pixels = candidate.crop((32, 24, 288, 216)).convert('RGB').resize((96, 72))
                    color_score = 0
                    for px in pixels.getdata():
                        spread = max(px) - min(px)
                        bright = max(px)
                        if spread > 26 and bright > 40:
                            color_score += spread + bright
                    score += color_score * 3
                if len(names) > 1:
                    # Prefer a legible shell/status row alongside both jobs.
                    status = inner.crop((0, 160, 256, 192)).resize((80, 12))
                    score += sum(v > 48 for v in status.get_flattened_data())
                if names == ('kaleido',):
                    pixels = candidate.crop((32, 24, 288, 216)).convert('RGB').resize((80, 60))
                    score += sum((max(p) - min(p)) > 60 for p in pixels.get_flattened_data())
                if config.get('capture_last') or score > best_score:
                    best, best_score = candidate, score
                if config.get('first_fractal'):
                    # Spectrum PLOT draws from bottom to top; row 8 only
                    # becomes active when the first 48-row scan is complete.
                    top = candidate.crop((32, 32, 288, 36)).convert('RGB')
                    if sum(max(v)>65 for v in top.get_flattened_data()) >= 12:
                        best = candidate
                        print('Fuse', names[0], 'first fractal completed', flush=True)
                        break
            if best is None:
                raise RuntimeError('screen unchanged from ZX-UX login')
            if config.get('first_fractal') and not any(max(v)>65 for v in best.crop((32,32,288,36)).convert('RGB').get_flattened_data()):
                raise RuntimeError('first fractal incomplete')
            destination.parent.mkdir(parents=True, exist_ok=True)
            best.save(destination)
            print('Fuse', '+'.join(names), '->', destination.relative_to(ROOT), flush=True)
        finally:
            if kb:
                kb.close()
            for proc in (fuse, xvfb):
                if proc and proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=3)


def add_source_links():
    """Add portable relative C source links to the Fuse gallery."""
    index = OUT / 'index.html'
    lines = index.read_text(encoding='utf-8').splitlines(keepends=True)
    sources = {}
    for path in sorted(SOURCES.glob('*/*.c')):
        name = ('maze1982' if path.parent.name == 'examples' and path.stem == 'maze'
                else 'maze1996' if path.parent.name == 'games' and path.stem == 'maze1982'
                else path.stem)
        sources[f'{path.parent.name}/{name}.png'] = [path]
    for a, b in PAIRS:
        sources[f'multitask/{a}-{b}-shell.png'] = [SOURCES / 'demos' / (n + '.c') for n in (a, b)]
    for i, line in enumerate(lines):
        for png, paths in sources.items():
            if f'<a href="{png}"' not in line:
                continue
            links = []
            for source in paths:
                if source.is_file():
                    href = quote(os.path.relpath(source, OUT).replace(os.sep, '/'), safe='/')
                    links.append(f'<a href="{escape(href, quote=True)}">C source: {escape(source.name)}</a>')
            if links:
                lines[i] = line.replace('</figcaption>', ' — ' + ', '.join(links) + '</figcaption>')
            break
    index.write_text(''.join(lines), encoding='utf-8')


def _capture_task(task):
    index, names, output, args, config = task
    local = argparse.Namespace(**vars(args))
    # Each process owns its own X display, SDL window and real Spectrum.
    local.display = args.display + 1 + index
    run_case(names, output, local, config)
    return '+'.join(names)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fuse', type=Path, required=True)
    p.add_argument('--rom', type=Path, default=ROOT / 'release/src/zx-ux/rom/48.rom')
    p.add_argument('--assets', type=Path, required=True)
    p.add_argument('--libdir', type=Path, default=None)
    p.add_argument('--only', default='')
    p.add_argument('--display', type=int, default=98)
    p.add_argument('--jobs', type=int, default=6)
    p.add_argument('--boot-wait', type=int, default=60)
    p.add_argument('--wait', type=int, default=4)
    p.add_argument('--speed', type=int, default=100)
    p.add_argument('--multitask-wait', type=int, default=60)
    a = p.parse_args()
    a.fuse = a.fuse.resolve()
    a.rom = a.rom.resolve()
    a.assets = a.assets.resolve()
    if a.libdir:
        a.libdir = a.libdir.resolve()
    only = set(a.only.split(',')) if a.only else None
    if not 1 <= a.jobs <= 16:
        p.error('--jobs must be from 1 to 16')
    tasks = []
    choices = list(captures())
    for name, category, config in choices:
        if only is not None and name not in only:
            continue
        tasks.append(((name,), OUT / category / (name + '.png'), {**config, **FUSE_CAPTURE.get(name, {})}))
    for pair in PAIRS:
        name = '-'.join(pair)
        if only is None or name in only:
            tasks.append((pair, OUT / 'multitask' / (name + '-shell.png'), {}))
    errors = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.jobs) as pool:
        pending = {pool.submit(_capture_task, (i, names, dest, a, config)): names
                   for i, (names, dest, config) in enumerate(tasks)}
        for future in concurrent.futures.as_completed(pending):
            names = pending[future]
            try:
                future.result()
            except Exception as exc:
                name = '+'.join(names)
                print('Fuse FAIL:', name, exc, file=sys.stderr, flush=True)
                errors.append(name)
    if only is not None:
        unknown = only - {n for n, _, _ in choices} - {'-'.join(p) for p in PAIRS}
        errors += sorted(unknown)
    count = write_gallery(OUT, 'Fuse — ZX Spectrum 48K')
    add_source_links()
    if count != 63:
        errors.append('expected 63 Fuse images, got %d' % count)
    print('Fuse captured', count, 'images; failures:', len(errors))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Capture real Fuse ZX Spectrum 48K screenshots of a freshly built C48 set.

Each capture boots the unmodified ZX-UX TZX and loads the selected SSX
via the kernel's /dev/cassette path. No simulated system calls or image
substitutions. Xvfb, Fuse SDL and Pillow must be installed externally.
"""
import argparse
import ctypes
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from PIL import ImageGrab, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'release/dist/sdk/bin/py'), str(ROOT / 'tools')]
from fuse_boot import (SCREEN_WIDTH, SCREEN_HEIGHT, SPECTRUM_X, SPECTRUM_Y,
                       zxux_login_match, send_rom_load)
from gallery import write_gallery
from portfolio import captures, BIN, DIST, PAIRS
import rtap

OUT = DIST / 'screenshots/fuse'


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
        names = {'\n': 'Return', ' ': 'space', '/': 'slash', '&': 'ampersand'}
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
        self.event('7' if name == 'ampersand' else ('Return' if name == 'Return' else name.lower()), True)
        time.sleep(pause)
        self.event('7' if name == 'ampersand' else ('Return' if name == 'Return' else name.lower()), False)
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
                       '--no-sound', '--tape', str(tape), '--auto-load']
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
                kb.key('\n', pause=.8)
                time.sleep(2.0)
            if len(names) == 1 and names[0] == '3dpaint':
                time.sleep(2)
                kb.type('q')
            # Real emulator timing; choose developed frames without filling the
            # gallery with the same boot/login screen.
            duration = args.multitask_wait if len(names) > 1 else args.wait
            best = None
            best_score = -1
            for _ in range(max(1, int(duration))):
                time.sleep(1)
                candidate = screenshot(display)
                changed = ImageChops.difference(candidate.convert('RGB'), login.convert('RGB'))
                bbox = changed.getbbox()
                if not bbox:
                    continue
                # Judge actual program pixels, not Fuse's coloured border.
                inner = candidate.crop((32, 24, 288, 216)).convert('L')
                score = sum(v > 48 for v in inner.resize((80, 60)).get_flattened_data())
                if len(names) > 1:
                    # Prefer a legible shell/status row alongside both jobs.
                    status = inner.crop((0, 160, 256, 192)).resize((80, 12))
                    score += sum(v > 48 for v in status.get_flattened_data())
                if score > best_score:
                    best, best_score = candidate, score
            if best is None:
                raise RuntimeError('screen unchanged from ZX-UX login')
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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fuse', type=Path, required=True)
    p.add_argument('--rom', type=Path, default=ROOT / 'release/src/zx-ux/rom/48.rom')
    p.add_argument('--assets', type=Path, required=True)
    p.add_argument('--libdir', type=Path, default=None)
    p.add_argument('--only', default='')
    p.add_argument('--display', type=int, default=98)
    p.add_argument('--boot-wait', type=int, default=60)
    p.add_argument('--wait', type=int, default=4)
    p.add_argument('--multitask-wait', type=int, default=60)
    a = p.parse_args()
    a.fuse = a.fuse.resolve()
    a.rom = a.rom.resolve()
    a.assets = a.assets.resolve()
    if a.libdir:
        a.libdir = a.libdir.resolve()
    only = set(a.only.split(',')) if a.only else None
    errors = []
    choices = list(captures())
    for name, category, config in choices:
        if only is not None and name not in only:
            continue
        try:
            run_case((name,), OUT / category / (name + '.png'), a, config)
        except Exception as exc:
            print('Fuse FAIL:', name, exc, file=sys.stderr)
            errors.append(name)
    for pair in PAIRS:
        name = '-'.join(pair)
        if only is None or name in only:
            try:
                run_case(pair, OUT / 'multitask' / (name + '-shell.png'), a)
            except Exception as exc:
                print('Fuse FAIL:', name, exc, file=sys.stderr)
                errors.append(name)
    if only is not None:
        unknown = only - {n for n, _, _ in choices} - {'-'.join(p) for p in PAIRS}
        if unknown:
            errors += sorted(unknown)
    count = write_gallery(OUT, 'Fuse — ZX Spectrum 48K')
    print('Fuse captured', count, 'images; failures:', len(errors))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())

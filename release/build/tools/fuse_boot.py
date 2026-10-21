#!/usr/bin/env python3
"""Verify an independent ZX Spectrum 48K tape boot in FUSE.

Start a checked FUSE SDL executable under Xvfb and use the real ROM to
load a TAP or TZX file. Save the captured screen only after its pixels
match the expected text rendered with the 48K ROM font.

All external tools and libraries must be inspected separately before
running this program. Keep them outside the ZX-UX Git checkout.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from PIL import ImageGrab

ROM_HASH = 'd55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42'
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
SPECTRUM_X = (SCREEN_WIDTH - 320) // 2 + 32
SPECTRUM_Y = (SCREEN_HEIGHT - 240) // 2 + 24
KEYS = {'j': 44, 'Control_L': 37, 'p': 33, 'Return': 36}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font_match(image, rom, phrase):
    """Find an exact 48K ROM-font text run on Spectrum character cells."""
    font = rom[0x3d00:0x4000]
    if len(font) != 768 or any(ord(c) < 32 or ord(c) > 127 for c in phrase):
        raise ValueError('Expected text must use the standard 48K ROM font')
    if not 5 <= len(phrase) <= 32:
        raise ValueError('Expected text must be between 5 and 32 characters')
    pix = image.convert('RGB').load()
    for row in range(24):
        for column in range(33 - len(phrase)):
            for i, char in enumerate(phrase):
                glyph = font[(ord(char) - 32) * 8:(ord(char) - 31) * 8]
                x = SPECTRUM_X + (column + i) * 8
                y = SPECTRUM_Y + row * 8
                ink = paper = None
                matches = True
                for dy, mask in enumerate(glyph):
                    for dx in range(8):
                        pixel = pix[x + dx, y + dy]
                        if mask & (128 >> dx):
                            if ink is None:
                                ink = pixel
                            elif ink != pixel:
                                matches = False
                                break
                        else:
                            if paper is None:
                                paper = pixel
                            elif paper != pixel:
                                matches = False
                                break
                    if not matches:
                        break
                if not matches or (ink is not None and ink == paper):
                    break
            else:
                return {'column': column, 'row': row}
    return None


# Checked login-screen markers from an actual ZX-UX v1 tape boot.
# The console uses a narrow screen font rather than the Spectrum ROM font.
# Coordinates apply to the fixed 900 by 700 virtual screen above.
ZXUX_LOGIN_MARKERS = (
    (322, 263, (
        '111010100000101010100000',
        '001010100000101010100000',
        '001001000000101001000000',
        '010001001110101001000000',
        '100010100000101010100000',
        '111010100000111010100000',
    )),
    (330, 295, (
        '111010100000101010100000',
        '001010100000101010100000',
        '001001000000101001000000',
        '010001001110101001000000',
        '100010100000101010100000',
        '111010100000111010100000',
    )),
    (322, 303, (
        '0100000000000100000000000000',
        '0100000000000000000000000000',
        '0100111001100100110000000000',
        '0100101010100100101001000000',
        '0100101010100100101000000000',
        '0110111001100100101001000000',
        '0000000011000000000000000000',
    )),
)


def zxux_login_match(image):
    """Match three checked 4-pixel console-font boot markers exactly."""
    pixels = image.convert('RGB').load()
    for x, y, rows in ZXUX_LOGIN_MARKERS:
        for dy, bits in enumerate(rows):
            for dx, expected in enumerate(bits):
                actual = pixels[x + dx, y + dy]
                lit = max(actual) > 64
                if lit != (expected == '1'):
                    return None
    return {'boot_banner': [322, 263], 'console_title': [330, 295],
            'login_prompt': [322, 303]}


def send_rom_load(display):
    """Type the Spectrum ROM LOAD command using XTEST under a US Xvfb map."""
    info = subprocess.run(['xwininfo', '-root', '-tree'], env=dict(os.environ, DISPLAY=display),
                          text=True, capture_output=True, check=True)
    windows = re.findall(r'^\s*(0x[0-9a-f]+)\s+"(Fuse[^"\n]*)"', info.stdout, re.M)
    if not windows:
        raise RuntimeError('FUSE window is missing')
    x11 = ctypes.CDLL('libX11.so.6')
    xtst = ctypes.CDLL('libXtst.so.6')
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XSetInputFocus.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    x11.XFlush.argtypes = [ctypes.c_void_p]
    xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    ptr = x11.XOpenDisplay(display.encode())
    if not ptr:
        raise RuntimeError('X display is unavailable')
    x11.XSetInputFocus(ptr, int(windows[0][0], 16), 1, 0)
    x11.XFlush(ptr)

    def key(name, down):
        xtst.XTestFakeKeyEvent(ptr, KEYS[name], int(down), 0)
        x11.XFlush(ptr)
        time.sleep(0.075)

    def chord(modifier, name):
        key(modifier, True)
        key(name, True)
        key(name, False)
        key(modifier, False)

    key('j', True)
    key('j', False)
    chord('Control_L', 'p')
    chord('Control_L', 'p')
    key('Return', True)
    key('Return', False)
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XCloseDisplay(ptr)


def run(args):
    fuse, romfile, tapefile, assets, libdir, screen = (
        args.fuse.resolve(), args.rom.resolve(), args.tape.resolve(),
        args.assets.resolve(), args.libdir.resolve(), args.screen.resolve())
    for file in (fuse, romfile, tapefile):
        if not file.is_file() or file.is_symlink():
            raise RuntimeError('A required input file is missing or linked')
    if not (assets / 'fuse.font').is_file() or not libdir.is_dir():
        raise RuntimeError('FUSE runtime assets or libraries are missing')
    if tapefile.suffix.lower() not in ('.tzx', '.tap'):
        raise RuntimeError('The input must be a TAP or TZX tape')
    rom = romfile.read_bytes()
    if len(rom) != 16384 or hashlib.sha256(rom).hexdigest() != ROM_HASH:
        raise RuntimeError('The 48K ROM does not match the verified copy')
    screen.parent.mkdir(parents=True, exist_ok=True)
    display = ':97'
    xvfb = None
    emulator = None
    errors = screen.with_suffix('.stderr.txt')
    stdout = screen.with_suffix('.stdout.txt')
    try:
        xvfb = subprocess.Popen(['Xvfb', display, '-screen', '0',
                                 f'{SCREEN_WIDTH}x{SCREEN_HEIGHT}x24', '-nolisten', 'tcp'],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        if xvfb.poll() is not None:
            raise RuntimeError('Virtual display did not start')
        env = dict(os.environ, DISPLAY=display, SDL_VIDEODRIVER='x11',
                   SDL_AUDIODRIVER='dummy', LD_LIBRARY_PATH=str(libdir))
        cmd = [str(fuse), '--machine', '48', '--rom-48', str(romfile),
               '--no-sound', '--tape', str(tapefile), '--auto-load']
        with stdout.open('wb') as out, errors.open('wb') as err:
            emulator = subprocess.Popen(cmd, cwd=assets, env=env,
                                        stdout=out, stderr=err)
            time.sleep(2)
            if emulator.poll() is not None:
                raise RuntimeError('FUSE ended before the tape could load')
            send_rom_load(display)
            deadline = time.monotonic() + args.wait
            while time.monotonic() < deadline:
                if emulator.poll() is not None:
                    raise RuntimeError('FUSE exited while checking the tape')
                time.sleep(2)
                picture = ImageGrab.grab(xdisplay=display)
                location = (zxux_login_match(picture)
                            if args.expect_zxux_login
                            else font_match(picture, rom, args.expected_text))
                if location:
                    picture.save(screen)
                    proof = {
                        'result': 'PASS', 'machine': 'ZX Spectrum 48K',
                        'emulator': str(fuse), 'rom_sha256': sha256(romfile),
                        'tape_sha256': sha256(tapefile),
                        'screen_sha256': sha256(screen),
                        'expected_text': ('ZX-UX login' if args.expect_zxux_login
                                          else args.expected_text),
                        'match_method': ('checked ZX-UX login screen markers'
                                         if args.expect_zxux_login
                                         else '48K ROM font'),
                        'text_position': location,
                    }
                    screen.with_suffix('.json').write_text(json.dumps(proof, indent=2) + '\n')
                    return proof
            picture.save(screen)
            raise RuntimeError('Expected ZX Spectrum screen text was not found')
    finally:
        for proc in (emulator, xvfb):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fuse', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--tape', type=Path, required=True)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--libdir', type=Path, required=True)
    parser.add_argument('--screen', type=Path, required=True)
    marker = parser.add_mutually_exclusive_group(required=True)
    marker.add_argument('--expected-text')
    marker.add_argument('--expect-zxux-login', action='store_true')
    parser.add_argument('--wait', type=int, default=30)
    args = parser.parse_args()
    if not 3 <= args.wait <= 240:
        parser.error('The boot wait must be from 3 to 240 seconds')
    try:
        result = run(args)
        print('PASS: independent FUSE tape boot:', json.dumps(result, sort_keys=True))
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print('FAIL: independent FUSE tape boot:', error, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

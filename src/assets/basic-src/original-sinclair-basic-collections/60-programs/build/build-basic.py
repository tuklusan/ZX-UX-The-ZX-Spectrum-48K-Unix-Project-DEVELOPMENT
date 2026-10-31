#!/usr/bin/env python3
"""Rebuild Spectrum BASIC tapes and optional FUSE screenshots from existing .bas files.

    python build/build-basic.py                         # all 60 tapes
    python build/build-basic.py 25-galaxians           # one tape
    python build/build-basic.py --screenshots 58-invaders --fuse /path/to/fuse-sdl

Output is staged under build/tmp/basic-output/, never over the historical BASIC files.
Screenshots require FUSE SDL, Xvfb, python-xlib, Pillow and the frozen SDK ROM.
The decoded .bas listings are not byte-exact originals: rebuilt tapes and captures
may differ from the original tapes and screenshots.
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

from basic_tape import tzx_from_listing

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / 'build' / 'tmp' / 'basic-output'
ROM = ROOT.parent.parent / 'zx-ux-sdk' / 'rom' / '48.rom'


def historical_name(folder):
    """Retain the old tape label when available, otherwise derive one."""
    path = folder / 'BASIC' / (folder.name + '.tzx')
    if path.is_file():
        buf = path.read_bytes()
        if buf[:11] == b'ZXTape!\x1a\x01\x14\x10' and len(buf) >= 29:
            name = buf[17:27].decode('latin-1').strip()
            if name:
                return name
    return folder.name.split('-', 1)[1].replace('-', ' ').title()[:10]


def replay_args(folder):
    """Reuse each preserved program's recorded timing and input recipe."""
    file = folder / 'BASIC' / 'REPLAY.sh'
    if not file.is_file():
        raise FileNotFoundError(f'{file}: no recorded replay recipe')
    text = file.read_text()
    marker = 'exec python3 "$ROOT/TOOLS/run_fuse_demo_v18.py"'
    if marker not in text:
        raise ValueError(f'{file}: unexpected replay format')
    words = shlex.split(text.split(marker, 1)[1].replace('\\\n', ' '))
    # Original tape is positional; use the newly rebuilt tape instead.
    if not words or not words[0].endswith('.tzx'):
        raise ValueError(f'{file}: tape input is not first')
    words.pop(0)
    # Override paths and display; keep the historically chosen input/timing flags.
    value_flags = {'--rom', '--fuse', '--out', '--display'}
    result = []
    i = 0
    while i < len(words):
        if words[i] in value_flags:
            i += 2
        else:
            result.append(words[i]); i += 1
    return result


def screenshot_targets(folder):
    """Map selected screenshots to the actual raw FUSE capture filenames."""
    notes = (folder / 'BASIC' / 'KEYS-AND-TIMING.TXT').read_text()
    matches = re.findall(
        r'SCREENSHOTS/([^\s/]+\.png)\s*\n\s*[^\n]*?source\s+\S+/([^\s/]+\.png)',
        notes,
    )
    if not matches:
        raise ValueError(f'{folder.name}: no recorded screenshot selection')
    return matches


def replay_script(name):
    return ("#!/bin/sh\nset -eu\n"
            "HERE=$(CDPATH= cd -- \"$(dirname -- \"$0\")\" && pwd)\n"
            "while [ \"$HERE\" != / ] && [ ! -f \"$HERE/build/build-basic.py\" ]; do\n"
            "    HERE=$(dirname \"$HERE\")\n"
            "done\n"
            "exec python3 \"$HERE/build/build-basic.py\" --screenshots "
            + shlex.quote(name) + " \"$@\"\n")


def build_one(folder, output, images, fuse, rom):
    name = folder.name
    bas = folder / 'BASIC' / (name + '.bas')
    if not bas.is_file():
        raise FileNotFoundError(bas)
    dest = output / name / 'BASIC'
    dest.mkdir(parents=True, exist_ok=True)
    tape = dest / (name + '.tzx')
    tape.write_bytes(tzx_from_listing(bas.read_text(encoding='utf-8-sig'), historical_name(folder)))
    raw = []
    if images:
        args = replay_args(folder)
        raw_dir = output / name / 'REPLAY-RAW'
        raw_dir.mkdir(parents=True, exist_ok=True)
        runner = Path(__file__).with_name('fuse_capture.py')
        display = ':' + str(27000 + int(name[:2]))
        cmd = [sys.executable, str(runner), str(tape), '--rom', str(rom),
               '--fuse', fuse, '--out', str(raw_dir), '--display', display] + args
        subprocess.run(cmd, check=True)
        raw = json.loads((raw_dir / 'test-info.json').read_text())
        shots = dest / 'SCREENSHOTS'
        shots.mkdir(exist_ok=True)
        for target, source in screenshot_targets(folder):
            src = raw_dir / source
            if not src.is_file():
                raise FileNotFoundError(f'{name}: expected FUSE screenshot {source}')
            shutil.copyfile(src, shots / target)
    (dest / 'README.TXT').write_text(
        f'{name}\nRebuilt from BASIC/{name}.bas using build/build-basic.py.\n'
        'The decoded listing does not preserve every original tape byte.\n'
        'The generated TZX is a non-auto-run Spectrum 48K BASIC tape.\n'
        'Load it with LOAD "" and then type RUN.\n'
        + ('SCREENSHOTS contains fresh, actual FUSE images.\n' if images else
           'To regenerate screenshots, run build-basic.py --screenshots.\n')
        + 'Historical BASIC/ originals are not modified by this builder.\n',
        encoding='utf-8')
    (dest / 'REPLAY.sh').write_text(replay_script(name), encoding='utf-8')
    notes = [f'{name} — generated run notes',
             'Tape: re-tokenized from the stored .bas listing; not a byte-identical original.',
             'Replay settings: the historical BASIC/REPLAY.sh file (when screenshots requested).']
    if images:
        notes.extend(['FUSE key events and capture times (seconds from runner start):'])
        notes.extend(f"  {x['seconds']:.3f} {x.get('key', x.get('symbol', x))}" for x in raw.get('keypress_events', []))
        notes.append('Screenshots:')
        for target, source in screenshot_targets(folder):
            match = next((x for x in raw.get('screenshot_timeline', []) if x['file'] == source), None)
            notes.append(f"  SCREENSHOTS/{target}: {source}" +
                         (f" at {match['seconds']:.3f} s" if match else ''))
    else:
        notes.append('FUSE not executed; no new screenshot or runtime check.')
    (dest / 'KEYS-AND-TIMING.TXT').write_text('\n'.join(notes) + '\n', encoding='utf-8')
    print(f'{name}: {tape} ({tape.stat().st_size} bytes)' +
          (' + captured screenshots' if images else ''))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('programs', nargs='*', help='numbered program folders; defaults to all 60')
    parser.add_argument('--screenshots', action='store_true', help='run recorded FUSE demonstrations')
    parser.add_argument('--fuse', default='fuse-sdl', help='FUSE SDL executable')
    parser.add_argument('--rom', type=Path, default=ROM, help='Spectrum 48K ROM')
    parser.add_argument('--output', type=Path, default=DEST, help='staging directory, never original BASIC')
    args = parser.parse_args()
    output = args.output.resolve()
    # No build may write to locked paths or replace historical files.
    choices = sorted((p for p in ROOT.iterdir() if re.match(r'^\d{2}-', p.name) and p.is_dir()),
                     key=lambda p: int(p.name[:2]))
    wanted = set(args.programs)
    unknown = wanted - {p.name for p in choices}
    if unknown:
        parser.error('unknown program(s): ' + ', '.join(sorted(unknown)))
    if output == ROOT or (ROOT in output.parents and ROOT / 'build' / 'tmp' not in output.parents):
        parser.error('output inside repository must be under build/tmp/')
    if not output.is_relative_to(ROOT) and output.is_relative_to(ROOT.parent.parent.parent):
        parser.error('output cannot be placed in a frozen repository path')
    if args.screenshots:
        if not args.rom.is_file():
            parser.error('Spectrum ROM missing: ' + str(args.rom))
        if not (shutil.which(args.fuse) or Path(args.fuse).is_file()):
            parser.error('FUSE SDL not found: ' + args.fuse)
    for folder in choices:
        if not wanted or folder.name in wanted:
            build_one(folder, output, args.screenshots, args.fuse, args.rom)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Collect real ZX-UX game frames through short and held-key input.

This probe does not decide full game parity from a boot or a nonblank frame.
The original Sinclair BASIC sources and screenshots are read-only inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


GAMES = ((25, 'galaxians'), (58, 'invaders'))
# These keys are read from the unchanged BASIC game controls, not guessed.
GAME_KEY_PLAN = {
    '25-galaxians': ('z', 'x', 'm'),
    '58-invaders': ('5', '8', '0'),
}
CHARSET_OFFSET = 32
CHARSET_SIZE = 96
# First two sprite definitions taken from the unchanged BASIC DATA lines.
UDG_EXPECTED = {
    '25-galaxians': {
        0x90: bytes((34, 35, 36, 62, 15, 7, 2, 14)),
        0x91: bytes((36, 196, 228, 252, 240, 224, 64, 112)),
    },
    '58-invaders': {
        0xA2: bytes((60, 140, 115, 51, 63, 111, 193, 192)),
        0x98: bytes((60, 49, 206, 204, 252, 246, 131, 3)),
    },
}


def check_udgs(memory, base: int, name: str) -> list[dict]:
    """Verify selected process-local sprite bytes against original DATA lines."""
    checks = []
    for code, expected in UDG_EXPECTED.get(name, {}).items():
        start = base + (code - 0x90) * 8
        valid = 0 <= start <= 65536 - 8
        actual = bytes(memory[start:start + 8]) if valid else b''
        checks.append({'spectrum_character': code,
                       'address': start, 'expected': expected.hex(),
                       'actual': actual.hex(),
                       'matches_original_data': actual == expected})
    return checks


def screen_cell(bitmap: bytes, row: int, col: int) -> bytes:
    """Fetch a cell from the Spectrum's interleaved 6144-byte bitmap."""
    if not (0 <= row < 24 and 0 <= col < 32) or len(bitmap) < 6144:
        raise ValueError('invalid Spectrum bitmap or cell')
    result = bytearray()
    for y in range(row * 8, row * 8 + 8):
        offset = ((y & 0xC0) << 5) | ((y & 0x07) << 8) | ((y & 0x38) << 2) | col
        result.append(bitmap[offset])
    return bytes(result)


def screen_letters(bitmap: bytes, font: bytes) -> list[str]:
    """Decode exact 8x8 glyph matches, never guess unknown graphics."""
    if len(font) != 768:
        raise ValueError('expected 768 printable font bytes')
    glyphs = {bytes(font[i * 8:(i + 1) * 8]): chr(i + CHARSET_OFFSET)
              for i in range(CHARSET_SIZE)}
    return [''.join(glyphs.get(screen_cell(bitmap, r, c), '?')
                    for c in range(32)) for r in range(24)]


def font_state(memory, chars_pointer: int, font: bytes) -> dict:
    """Compare the live process font with the expected source font."""
    start = chars_pointer + 256
    if not 0 <= start <= len(memory) - len(font):
        return {'font_intact': False, 'font_difference_count': len(font),
                'font_first_differences': ['pointer_outside_memory']}
    changed = [i for i, (found, expected) in enumerate(
        zip(memory[start:start + len(font)], font)) if found != expected]
    return {'font_intact': not changed, 'font_difference_count': len(changed),
            'font_first_differences': changed[:16]}


def word_at(memory, address: int) -> int:
    return int(memory[address]) | (int(memory[address + 1]) << 8)


def capture(runner, font: bytes, directory: Path, name: str, label: str) -> dict:
    import rvm
    bitmap, border = runner.picture()
    if len(bitmap) != 6912:
        raise ValueError(f'{name}: expected 6912-byte display, got {len(bitmap)}')
    png = directory / f'{name}-{label}.png'
    rvm.write_png(bitmap, str(png), border)
    text = screen_letters(bitmap, font)
    status = runner.fg.status if runner.fg else None
    udg_base = word_at(runner.session.m.mem, 0x5C7B)
    charset_base = word_at(runner.session.m.mem, 0x5C36)
    return {
        'phase': label,
        'native_png': png.name,
        'screen_sha256': hashlib.sha256(bitmap).hexdigest(),
        'active_pixels': sum(int(byte).bit_count() for byte in bitmap[:6144]),
        'border': int(border),
        'chars_pointer': charset_base,
        'font_state': font_state(runner.session.m.mem, charset_base, font),
        'udg_pointer': udg_base,
        'known_udg_glyphs': check_udgs(runner.session.m.mem, udg_base, name),
        'keyboard_state': runner.session.kb.state,
        'keyboard_interrupt_scans': runner.session.m.ints,
        'foreground_status': status,
        'active_program_frames': runner.session.m.frame - (runner.fg.started or runner.session.m.frame),
        'text_lines': text,
        'score_label_visible': any('SCORE:' in line for line in text),
        'reserve_label_visible': any('ROCKET RESERVE:' in line for line in text),
    }


def advance(runner, frames: int) -> None:
    for _ in range(frames):
        runner.frame()


def run_game(ssx: Path, system: Path, font: bytes, original: Path, directory: Path) -> dict:
    import rvm
    import zxux
    options = rvm.Options()
    options.prog = str(ssx)
    options.system = str(system)
    options.headless = True
    options.cache = True
    runner = rvm.Runner(options)
    runner.start()
    # Galaxians relies on the Issue 2 MIC/EAR feedback level.
    # Select a supported ULA profile, without changing reads or game code.
    ula_issue = 2 if ssx.stem.startswith('25-galaxians') else 3
    runner.session.m.ula_issue = ula_issue
    for _ in range(9000):
        runner.frame()
        if runner.fg and runner.fg.started is not None:
            break
    else:
        raise RuntimeError(f'{ssx.name}: real ZX-UX program did not start')
    name = ssx.stem.replace('-tape', '')
    original_hash = hashlib.sha256(original.read_bytes()).hexdigest() if original.is_file() else None
    report = {'program': name, 'source_binary': ssx.name,
              'ssx_sha256': hashlib.sha256(ssx.read_bytes()).hexdigest(),
              'original_screenshot': str(original),
              'original_screenshot_sha256': original_hash,
              'ula_input': 'native emulator', 'ula_issue': ula_issue,
              'captures': []}
    advance(runner, 70)
    report['captures'].append(capture(runner, font, directory, name, 'idle'))
    # Both preserved demonstrations begin with a SPACE key to start the game.
    runner.session.kb.add([('press', zxux.char_keys(' '), 24)])
    advance(runner, 24)
    report['captures'].append(capture(runner, font, directory, name, 'start-held'))
    advance(runner, 36)
    report['captures'].append(capture(runner, font, directory, name, 'start-released'))
    # These are physical matrix holds, not buffered input characters.
    key_plan = tuple((key, 15 if index == 2 else 24)
                     for index, key in enumerate(GAME_KEY_PLAN[name]))
    for letter, hold in key_plan:
        runner.session.kb.add([('press', zxux.char_keys(letter), hold)])
        advance(runner, hold)
        report['captures'].append(capture(runner, font, directory, name, letter + '-held'))
        advance(runner, 36)
        report['captures'].append(capture(runner, font, directory, name, letter + '-released'))
    report['capture_count'] = len(report['captures'])
    report['key_plan'] = ['SPACE'] + [key for key, _ in key_plan]
    report['start_screen_changed'] = (
        report['captures'][0]['screen_sha256'] !=
        report['captures'][2]['screen_sha256'])
    report['start_advanced_to_gameplay'] = 'not established'
    report['original_reference_available'] = original_hash is not None
    report['sprite_data_correct_at_end'] = all(
        g['matches_original_data'] for g in report['captures'][-1]['known_udg_glyphs'])
    report['all_frames_nonblank'] = all(x['active_pixels'] > 0 for x in report['captures'])
    report['font_intact_across_all_frames'] = all(
        frame['font_state']['font_intact'] for frame in report['captures'])
    if not report['font_intact_across_all_frames']:
        raise AssertionError(f'{name}: native process modified its character font')
    report['screen_changed_after_input'] = any(
        x['screen_sha256'] != report['captures'][0]['screen_sha256']
        for x in report['captures'][1:])
    report['visual_parity'] = 'not established; inspect native PNG beside the original'
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--trial', type=Path, default=Path('trial-result'))
    args = parser.parse_args()
    root, trial = args.root.resolve(), args.trial.resolve()
    sys.path.insert(0, str(root / 'dist/sdk/bin/py'))
    import rvm  # noqa: F401 -- also used by run_game and capture
    archive = root / 'experiments/hisoft-rbc-2026-10-22/rbc-sinclair-font-checkpoint-2026-10-22.zip'
    with zipfile.ZipFile(archive) as zf:
        font = zf.read('rbc/font32.bin')
    directory = trial / 'rbc-game-probe'
    directory.mkdir(parents=True, exist_ok=True)
    system = root / 'dist/zx-ux/tzx/ZX-UX.tzx'
    results = []
    for number, short_name in GAMES:
        name = f'{number:02d}-{short_name}'
        binary = trial / (name + '-tape.ssx')
        if not binary.is_file():
            continue  # The other matrix shards do not compile this game.
        original = root / f'src/bonus/60-programs/{name}/BASIC/SCREENSHOTS/02-MAIN.png'
        results.append(run_game(binary, system, font, original, directory))
    destination = directory / 'report.json'
    destination.write_text(json.dumps(results, indent=2) + '\n')
    for row in results:
        print(f"PROBE {row['program']}: {row['capture_count']} actual native frames, "
              f"screen_changed={row['screen_changed_after_input']}, "
              f"nonblank={row['all_frames_nonblank']}", flush=True)
    print(f'Native game probe results: {destination}', flush=True)


if __name__ == '__main__':
    main()

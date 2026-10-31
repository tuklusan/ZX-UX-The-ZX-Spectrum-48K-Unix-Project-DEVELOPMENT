"""Package already-accepted BASIC games without recompiling archival input."""
from __future__ import annotations

import re
import shutil
from pathlib import Path
import sys

SDK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SDK))
import rld
import rtap


def collections(source: Path):
    base = source / 'assets/basic-src'
    archive = base / 'original-sinclair-basic-collections'
    if archive.is_symlink() or (archive.exists() and not archive.is_dir()):
        raise ValueError('unsafe BASIC collections directory: ' + str(archive))
    seen = set()
    if archive.is_dir():
        for folder in sorted(archive.iterdir()):
            if folder.is_symlink():
                raise ValueError('linked BASIC collection not permitted: ' + str(folder))
            if not folder.is_dir():
                continue  # collection preparation guide and other source notes
            if not re.fullmatch(r'[a-zA-Z0-9_.-]+', folder.name):
                raise ValueError('unsafe BASIC collection name: ' + folder.name)
            if folder.name != '60-programs':
                # Other original collections remain archival until RBC verdicts
                # appear. Their BASIC programs are not silently compiled.
                games = (p for p in folder.iterdir() if p.is_dir() and
                         re.fullmatch(r'[0-9][0-9]-.+', p.name))
                if not any((game / 'bin' / (game.name + '.ssx')).is_file() or
                           (game / 'bin/README.md').is_file() for game in games):
                    continue
            seen.add(folder.name)
            yield folder.name, folder
    if base.is_dir():
        for folder in sorted(base.iterdir()):
            if folder.name == archive.name:
                continue
            if not folder.is_dir() or folder.is_symlink() or folder.name in seen:
                raise ValueError('unsafe or duplicate BASIC collection: ' + str(folder))
            if not re.fullmatch(r'[a-zA-Z0-9_.-]+', folder.name):
                raise ValueError('unsafe BASIC collection name: ' + folder.name)
            seen.add(folder.name)
            yield folder.name, folder


def tape_name(name: str) -> str:
    # The original two-digit game ID remains unique even if titles truncate.
    value = ''.join(c for c in name.upper() if c.isascii() and c.isalnum())
    if not 1 <= len(value) or not value[:2].isdigit():
        raise ValueError('game needs a stable two-digit tape ID: ' + name)
    return value[:10]


def package(source: Path, stage: Path):
    seen_collections = 0
    for collection, root in collections(source):
        seen_collections += 1
        games = sorted(p for p in root.iterdir() if p.is_dir() and
                       re.fullmatch(r'[0-9][0-9]-.+', p.name))
        if collection == '60-programs' and [int(p.name[:2]) for p in games] != list(range(1, 61)):
            raise ValueError('expected exactly 60 historical BASIC games')
        if not games:
            raise ValueError('empty BASIC collection: ' + collection)
        tape_names = set()
        base = stage / 'assets/rbc-bin' / collection
        (base / 'ssx').mkdir(parents=True, exist_ok=True)
        (base / 'tzx').mkdir(parents=True, exist_ok=True)
        for game in games:
            if game.is_symlink():
                raise ValueError('linked BASIC game not permitted')
            folder = game / 'BASIC'
            bas = list(folder.glob('*.bas'))
            tzx = list(folder.glob('*.tzx'))
            if len(bas) != 1 or len(tzx) != 1 or bas[0].stem != game.name or tzx[0].stem != game.name:
                raise ValueError('missing or ambiguous original BAS/TZX: ' + game.name)
            target = stage / 'assets/basic-src' / collection / game.name
            target.mkdir(parents=True, exist_ok=True)
            for original in (bas[0], tzx[0]):
                if original.is_symlink():
                    raise ValueError('linked BASIC input')
                shutil.copyfile(original, target / original.name)
            for png in sorted((folder / 'SCREENSHOTS').glob('*.png')):
                if png.is_symlink():
                    raise ValueError('linked BASIC screenshot')
                dst = (stage / 'screenshots/basic-original' / collection / game.name / png.name)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(png, dst)
            executable = game / 'bin' / (game.name + '.ssx')
            reason = game / 'bin/README.md'
            if executable.is_file() == reason.is_file() or executable.is_symlink() or reason.is_symlink():
                raise ValueError('BASIC result must be precisely one SSX or README: ' + game.name)
            if reason.is_file():
                continue
            data = executable.read_bytes()
            info = rld.parse_ssx(data)
            required = rtap.need(data)
            if max(required, len(data)) > 14000:
                raise ValueError('BASIC accepted SSX exceeds 14K: ' + game.name)
            (base / 'ssx' / executable.name).write_bytes(data)
            label = tape_name(game.name)
            if label in tape_names:
                raise ValueError('duplicate BASIC cassette name: ' + label)
            tape_names.add(label)
            header, payload = rtap.records(data, label)
            assert int.from_bytes(header[12:14], 'little') == len(data)
            assert int.from_bytes(header[14:16], 'little') == required
            assert all(rtap._parity_ok(block) for block in (header, payload))
            title = ('ZX-UX BASIC ' + game.name).encode('ascii')
            if len(title) > 255:
                raise ValueError('tape title exceeds limit')
            head = b'ZXTape!\x1a\x01\x14' + bytes((0x30, len(title))) + title
            tape = base / 'tzx' / (game.name + '.tzx')
            rtap.write(str(tape), head, [(1000, header), (2000, payload)])
            _, blocks = rtap.tzx_blocks(tape.read_bytes())
            if len(blocks) != 2 or blocks[0][1] != header or blocks[1][1] != payload:
                raise ValueError('BASIC cassette verification failed: ' + game.name)
    return seen_collections

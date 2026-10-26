#!/usr/bin/env python3
"""Restore the exact historical RBC core from DEVELOPMENT main Git history.

No compiler output or original game is added to version control. The reviewed
preparation stages rebuild a private build/tmp checkpoint from historical blobs.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

from prepare_rbc import prepare
from finish_rbc import finish

REVISION = '441db54e06fed624973baff8dc9e01c195e98424'
HISTORICAL_DIRECTORY = 'experiments/hisoft-rbc-2026-10-22/temporary-checkpoint'
EXPECTED_SHA256 = {
    'rbc.py': 'b82c1c933a7234f02becef8e73b1ae5efb54db99a12e70f82d07f34ebcb243eb',
    'memory_safety.py': 'e9025a0483c18597641b016b62ca0f734d9e973cf9376d4ea6838eab9d0481f8',
    'font32.b64': 'dfd241dc3fe9086db82caf97418228f62cc00deffbea29a532be99413a3faf65',
}
REPOSITORY = 'https://github.com/tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT.git'


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          capture_output=True).stdout


def restore(root: Path, output: Path, stage: Path | None = None) -> dict[str, str]:
    root = root.resolve()
    stage = (stage or Path(__file__).resolve().parent).resolve()
    output = output.resolve()
    if git(root, 'remote', 'get-url', 'origin').decode().strip() != REPOSITORY:
        raise ValueError('origin is not canonical DEVELOPMENT repository')
    git(root, 'merge-base', '--is-ancestor', REVISION, 'HEAD')
    if output.exists():
        raise FileExistsError('refusing to overwrite compiler checkpoint: ' + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.rbc-history-', dir=output.parent))
    try:
        folder = temporary / 'rbc'
        folder.mkdir()
        for name, expected in EXPECTED_SHA256.items():
            contents = git(root, 'show', f'{REVISION}:{HISTORICAL_DIRECTORY}/{name}')
            actual = hashlib.sha256(contents).hexdigest()
            if actual != expected:
                raise ValueError(f'historical {name} SHA-256 mismatch: {actual}')
            (folder / name).write_bytes(contents)
        font = base64.b64decode((folder / 'font32.b64').read_bytes(), validate=True)
        if len(font) != 768 or hashlib.sha256(font).hexdigest() != (
                '7b8faa46ee8359ea1cf141a85f618f9f3716334495f3c5c107bb1e5cb86cc468'):
            raise ValueError('historical 768-byte font digest mismatch')
        (folder / 'font32.bin').write_bytes(font)
        prepare(temporary, stage)
        finish(temporary, stage)
        for path in folder.glob('*.py'):
            compile(path.read_bytes(), str(path), 'exec')
        temporary.rename(output)
        return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((output / 'rbc').iterdir()) if p.is_file()}
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path,
                        default=Path(__file__).resolve().parents[3])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = args.output or args.root / 'build/tmp/rbc-checkpoint-recovered'
    digests = restore(args.root, output)
    print(f'RBC_HISTORY_RESTORED files={len(digests)} revision={REVISION} '
          f'compiler_sha256={digests["rbc.py"]}')


if __name__ == '__main__':
    main()

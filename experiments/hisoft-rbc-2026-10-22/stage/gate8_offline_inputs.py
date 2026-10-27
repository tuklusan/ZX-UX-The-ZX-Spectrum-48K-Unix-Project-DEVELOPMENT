#!/usr/bin/env python3
"""Restore locked Gate 8 inputs from offline ZIP archives and Git history.

No external network access, original BASIC changes or checked-in compiler
files. Every upstream Python file is checked by its locked Git blob SHA.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))

from hisoft_frontend_inputs import (FRONTEND, REVISION, convert_tzx_to_tap,
                                    git_blob)
from gate8_native_whole_optimizer import _LOCKED, _LOCKED_REVISION
from recover_rbc_checkpoint import restore


class OfflineInputsError(ValueError):
    """The supplied archive cannot establish a locked upstream identity."""


def verified_zip_sources(archive: Path, subdir: str,
                         expected: dict[str, str]) -> dict[str, bytes]:
    """Read only hash-verified Python files, never extract untrusted ZIP paths."""
    if not expected:
        raise OfflineInputsError('no expected source identities')
    result = {}
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.infolist()
        for filename, sha in expected.items():
            matches = [item for item in members
                       if not item.is_dir() and
                       item.filename.endswith('/' + subdir + filename)]
            if len(matches) != 1:
                raise OfflineInputsError(f'missing or duplicate locked source: {filename}')
            member = matches[0]
            prefix = member.filename[:-(len(subdir) + len(filename))]
            if (not prefix or not prefix.endswith('/') or
                    any(part in ('', '.', '..') for part in prefix[:-1].split('/')) or
                    member.file_size > 1_000_000):
                raise OfflineInputsError('unsafe or oversized upstream ZIP entry')
            raw = bundle.read(member)
            if git_blob(raw) != sha:
                raise OfflineInputsError(f'locked Git blob mismatch: {filename}')
            result[filename] = (prefix, raw)
    prefixes = {entry[0] for entry in result.values()}
    if len(prefixes) != 1:
        raise OfflineInputsError('upstream ZIP files came from different trees')
    return {name: raw for name, (_, raw) in result.items()}


def prepare_offline(root: Path, frontend_zip: Path, optimizer_zip: Path,
                    compiler_tzx: Path, output: Path) -> dict[str, str]:
    """Stage a complete isolated checkpoint, then publish it atomically."""
    root, output = root.resolve(), output.resolve()
    if output.exists():
        raise FileExistsError('refusing to overwrite Gate 8 inputs: ' + str(output))
    frontend = verified_zip_sources(frontend_zip, '', FRONTEND)
    optimizer = verified_zip_sources(optimizer_zip, 'upeepz80/', _LOCKED)
    tape = convert_tzx_to_tap(compiler_tzx.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='.rbc-gate8-', dir=output.parent))
    try:
        restore(root, temp / 'checkpoint')
        fdir = temp / 'upstream-pyhsb'
        udir = temp / 'upstream-upeepz80' / 'upeepz80'
        fdir.mkdir()
        udir.mkdir(parents=True)
        for filename, raw in frontend.items():
            (fdir / filename).write_bytes(raw)
        for filename, raw in optimizer.items():
            (udir / filename).write_bytes(raw)
        (temp / 'hisoft48.tap').write_bytes(tape)
        temp.rename(output)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return {
        'RBC_G8_CHECKPOINT': str(output / 'checkpoint' / 'rbc'),
        'RBC_G8_FRONTEND': str(output / 'upstream-pyhsb'),
        'RBC_G8_TAPE': str(output / 'hisoft48.tap'),
        'RBC_G8_OPTIMIZER': str(output / 'upstream-upeepz80'),
        'frontend_revision': REVISION,
        'optimizer_revision': _LOCKED_REVISION,
        'tape_sha256': hashlib.sha256(tape).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--frontend-zip', type=Path, required=True)
    parser.add_argument('--optimizer-zip', type=Path, required=True)
    parser.add_argument('--compiler-tzx', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for key, value in prepare_offline(args.root, args.frontend_zip,
                                      args.optimizer_zip, args.compiler_tzx,
                                      args.output).items():
        print(f'{key}={value}')


if __name__ == '__main__':
    main()

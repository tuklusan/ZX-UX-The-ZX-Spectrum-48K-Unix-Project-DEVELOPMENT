"""Exact existing-SSX baselines and native typed-program optimizer measurements.

Published native programs are historical size baselines, NOT proof that the
current HiSoft compiler has passed the full-program optimizer gate. Never
supply or infer post-optimization values for an unoptimized published file.
This tool creates no committed result ledger and changes no game inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


class NativeSizeError(ValueError):
    """A native input or size comparison cannot be trusted."""


def dimensions(payload: bytes, rld) -> dict:
    """Return measured file/image/BSS/stack/total without estimating bytes."""
    if not isinstance(payload, bytes) or not payload:
        raise NativeSizeError('native image must contain linked SSX bytes')
    try:
        parsed = rld.parse_ssx(payload)
        image, bss, stack = parsed['image'], parsed['bss'], parsed['stack']
    except (rld.LinkError, ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        raise NativeSizeError('invalid native SSX image') from exc
    if (not isinstance(image, bytes) or
            not all(isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 65535
                    for v in (bss, stack))):
        raise NativeSizeError('invalid native memory extents')
    total = len(image) + bss + stack
    return {'file_bytes': len(payload), 'image_bytes': len(image),
            'bss_bytes': bss, 'stack_bytes': stack, 'total_bytes': total,
            'admission_bytes': max(total, len(payload)),
            'sha256': hashlib.sha256(payload).hexdigest()}


def typed_pair(plain: bytes, optimized: bytes, rld, *,
               source_verified: bool, native_behavior_verified: bool) -> dict:
    """Report both linked variants, never granting unsupported runtime proof."""
    if source_verified is not True:
        raise NativeSizeError('typed complete original source required')
    pre, post = dimensions(plain, rld), dimensions(optimized, rld)
    return {'kind': 'source-owned-native-pair', 'pre_native': pre,
            'post_native': post,
            'file_savings_bytes': pre['file_bytes'] - post['file_bytes'],
            'memory_savings_bytes': pre['admission_bytes'] - post['admission_bytes'],
            'native_behavior_verified': native_behavior_verified is True,
            'upeepz80_revision_verified': False}


def published_baselines(root: Path, rld) -> dict:
    """Inventory the 60 original games without calling them post-optimizer outputs."""
    folder = root / 'src/bonus/60-programs'
    games = sorted(d for d in folder.iterdir()
                   if d.is_dir() and len(d.name) > 3 and
                   d.name[:2].isdigit() and d.name[2] == '-')
    if len(games) != 60:
        raise NativeSizeError('expected exactly 60 original games')
    sizes = []
    for game in games:
        stem = game.name
        if not (game / 'BASIC' / (stem + '.bas')).is_file():
            raise NativeSizeError(f'{stem}: original BAS is missing')
        if not (game / 'BASIC' / (stem + '.tzx')).is_file():
            raise NativeSizeError(f'{stem}: original TZX is missing')
        bin_dir = game / 'bin'
        outputs = sorted(p for p in bin_dir.iterdir() if p.is_file())
        if len(outputs) != 1:
            raise NativeSizeError(f'{stem}: expected exactly one published output')
        output = outputs[0]
        if output.name == stem + '.ssx':
            sizes.append({'game': stem, **dimensions(output.read_bytes(), rld)})
        elif output.name != 'README.md':
            raise NativeSizeError(f'{stem}: unrecognized published output')
    if len(sizes) != 24:
        raise NativeSizeError('published native count differs from 24 checked games')
    return {'kind': 'published-existing-native-baseline',
            'games': len(games), 'original_bas': len(games),
            'original_tzx': len(games), 'ssx': len(sizes),
            'readmes': len(games) - len(sizes), 'measurements': sizes,
            'post_upeep': None, 'optimizer_savings': None,
            'native_behavior_verified': False, 'whole_program_optimized': False}


def main() -> None:
    import sys
    sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
    import rld
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(published_baselines(args.root, rld), sort_keys=True))


if __name__ == '__main__':
    main()

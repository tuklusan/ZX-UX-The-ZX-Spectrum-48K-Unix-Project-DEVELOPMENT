#!/usr/bin/env python3
"""Build individually playable Forth tapes using a staged ZX-UX SDK.

Build scripts may call build(stage_sdk, programs, dest), as with c48build.
For local development, --sdk can point to a read-only SDK containing ras,
rld and rtap; rfc and its runtime are loaded from this tool's sibling SDK.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


def build(stage_sdk: Path, programs: Path, dest: Path, *, stack: int = 512):
    """Recursively build .fth sources into dest/ssx and dest/tzx; return count.

    Names follow source stems, with the same ten-character cassette limit
    as c48build. Validate all names before creating any output.
    """
    stage_sdk, programs, dest = map(Path, (stage_sdk, programs, dest))
    if not programs.is_dir():
        raise ValueError('Forth source directory not found: ' + str(programs))
    if not 0 <= stack <= 65535:
        raise ValueError('Stack size must be between 0 and 65535')
    for module in ('ras.py', 'rld.py', 'rtap.py'):
        if not (stage_sdk / module).is_file():
            raise ValueError('SDK is missing ' + module + ': ' + str(stage_sdk))
    choices = {}
    for source in sorted(programs.rglob('*.fth')):
        name = source.stem
        if name in choices:
            raise ValueError('Duplicate Forth program name: ' + name)
        if not 1 <= len(name) <= 10 or not all(32 < ord(c) < 127 and c != '/' for c in name):
            raise ValueError('Invalid cassette program name (1..10 printable ASCII characters): ' + name)
        choices[name] = source
    if not choices:
        raise ValueError('No .fth sources found: ' + str(programs))

    # The complete staged SDK is preferred. The sibling supplies rfc when
    # developing against an SDK that has not yet incorporated Forth.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    sys.path.insert(0, str(stage_sdk.resolve()))
    import rtap
    from rfc import driver

    ssxdir, tzxdir = dest / 'ssx', dest / 'tzx'
    ssxdir.mkdir(parents=True, exist_ok=True)
    tzxdir.mkdir(parents=True, exist_ok=True)
    for name, source in sorted(choices.items()):
        try:
            _, data = driver.build(source, stack=stack, sdk=stage_sdk)
        except driver.ForthError as exc:
            raise ValueError('Compiler rejected %s: %s' % (source, exc)) from exc
        hdr, code = rtap.records(data, name)
        title = ('ZX-UX Forth ' + name).encode('ascii')
        head = b'ZXTape!\x1a\x01\x14' + bytes((0x30, len(title))) + title
        (ssxdir / (name + '.ssx')).write_bytes(data)
        rtap.write(str(tzxdir / (name + '.tzx')), head, [(1000, hdr), (2000, code)])
    return len(choices)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', type=Path, default=Path(os.environ.get(
        'ZXUX_SDK', Path(__file__).resolve().parents[1])),
        help='SDK containing ras.py, rld.py and rtap.py (default: ZXUX_SDK or sibling SDK)')
    parser.add_argument('--stack', type=lambda value: int(value, 0), default=512,
                        help='return-stack reservation in bytes (default: 512)')
    parser.add_argument('programs', type=Path, help='directory searched recursively for .fth files')
    parser.add_argument('dest', type=Path, help='output directory for ssx/ and tzx/')
    args = parser.parse_args(argv)
    try:
        count = build(args.sdk, args.programs, args.dest, stack=args.stack)
    except (OSError, ValueError, RuntimeError) as exc:
        print('forthbuild: ' + str(exc), file=sys.stderr)
        return 1
    print('Built %d Forth program(s) in %s' % (count, args.dest))
    return 0


if __name__ == '__main__':
    sys.exit(main())

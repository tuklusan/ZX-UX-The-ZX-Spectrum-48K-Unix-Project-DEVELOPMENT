#!/usr/bin/env python3
"""Offline builder for ZX-UX, its standalone SDK and individual program tapes.

Run from any directory: python3 release/build/build.py
Optional: --sjasm /path/to/approved/sjasmplus
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parent
ROOT = RELEASE.parent
TMP = HERE / 'tmp'
SOURCE = RELEASE / 'src'
DIST = RELEASE / 'dist'


def require(cond, message):
    if not cond:
        raise RuntimeError(message)


def snapshot_inputs():
    # Keep fingerprints in memory; source and output digests never enter release/.
    import hashlib
    paths = sorted(p for p in SOURCE.rglob('*') if p.is_file())
    return {p.relative_to(SOURCE): hashlib.sha256(p.read_bytes()).digest() for p in paths}


def run(cmd):
    result = subprocess.run([str(part) for part in cmd], cwd=ROOT, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.stdout:
        print(result.stdout, end='')
    require(result.returncode == 0, 'Command failed: ' + str(cmd))


def stage_inputs():
    for fromdir, todir in ((SOURCE / 'zx-ux', TMP / 'src'),
                           (SOURCE / 'zx-ux-sdk', TMP / 'sdk')):
        if todir.exists():
            shutil.rmtree(todir)
        shutil.copytree(fromdir, todir)
    (TMP / 'build').mkdir(parents=True, exist_ok=True)
    rom = TMP / 'sdk/rom'
    rom.mkdir(exist_ok=True)
    shutil.copyfile(SOURCE / 'zx-ux/rom/48.rom', rom / '48.rom')
    shutil.copyfile(SOURCE / 'zx-ux/font4x8.bin', rom / 'font4x8.bin')


def verify_tape_and_compiled_pairs(boot: Path, entries: Path):
    sys.path.insert(0, str(TMP / 'sdk'))
    import rtap
    raw = boot.read_bytes()
    parts = []
    pos = 0
    while pos < len(raw):
        require(pos + 2 <= len(raw), 'Truncated system TAP')
        n = int.from_bytes(raw[pos:pos+2], 'little')
        pos += 2
        require(n >= 2 and pos + n <= len(raw), 'Invalid system TAP block')
        data = raw[pos:pos+n]
        pos += n
        require(not (__import__('functools').reduce(lambda x,y:x^y,data,0)), 'System TAP parity failure')
        parts.append(data)
    require(len(parts) == 4, 'Merged TAP must contain BASIC and exactly one CODE block')
    require(parts[2][1] == 3 and parts[2][2:7] == b'ZX-UX', 'Merged TAP CODE header missing')
    expected_image = (TMP / 'build/merged-image.bin').read_bytes()
    require(parts[3][1:-1] == expected_image, 'Merged TAP CODE differs from linked image')
    ssx = entries / 'ssx'
    tzx = entries / 'tzx'
    names = {p.stem for p in ssx.glob('*.ssx')}
    require(names and names == {p.stem for p in tzx.glob('*.tzx')}, 'Missing program/tape pair')
    for name in sorted(names):
        _, records = rtap.tzx_blocks((tzx / (name + '.tzx')).read_bytes())
        require(len(records) == 2, 'Each program tape must hold one executable: ' + name)
        data = (ssx / (name + '.ssx')).read_bytes()
        require(records[1][1][1:-1] == data, 'Tape differs from built executable: ' + name)
    return len(names)


def build(sjasm: str):
    require(SOURCE.is_dir(), 'Missing release/src')
    require(os.path.isfile(sjasm) and os.access(sjasm, os.X_OK),
            'SJASMPlus 1.24.0 required locally; set --sjasm or put it in PATH')
    version = subprocess.run([sjasm, '--version'], capture_output=True, text=True)
    require(version.returncode == 0 and 'v1.24.0' in version.stdout + version.stderr,
            'SJASMPlus 1.24.0 version check failed')
    TMP.mkdir(parents=True, exist_ok=True)
    source_before = snapshot_inputs()
    candidate = TMP / 'dist-candidate'
    if candidate.exists():
        shutil.rmtree(candidate)
    stage_inputs()
    run([sys.executable, HERE / 'osbuild.py', sjasm])
    os_output = TMP / 'build'
    from turbo_boot_build import create_tzx
    from turbo_verify import check_tzx
    from osbuild import mkfs, program_list
    import re
    syms = {}
    for line in (TMP / 'src/unix.sym').read_text().splitlines():
        m = re.match(r'(\S+): EQU 0x([0-9A-Fa-f]+)', line)
        if m:
            syms[m.group(1)] = int(m.group(2), 16)
    require('LOWK' in syms and 'kend' in syms, 'Missing final boot layout symbols')
    fs_image, _, free, _ = mkfs(syms, program_list())
    require(fs_image == (os_output/'fs.img').read_bytes(), 'Staged FS image not reproducible')
    turbo, _, _ = create_tzx(sjasm, syms, syms['kend']-0x6000,
                              free, output_name='ZX-UX.tzx')
    check_tzx(turbo, (os_output/'merged-image.bin').read_bytes(),
              (os_output/'turbo_boot.bin').read_bytes(), load_base=syms['LOWK'])
    from c48build import build as build_c48
    from sdkpack import pack as pack_sdk
    target = candidate / 'zx-ux'
    target.mkdir(parents=True)
    shutil.copyfile(os_output / 'ZX-UX.tap', target / 'ZX-UX.tap')
    shutil.copyfile(os_output / 'ZX-UX.tzx', target / 'ZX-UX.tzx')
    source_assets = SOURCE / 'assets/c48-src'
    c48dir = candidate / 'assets/c48-bin'
    n = build_c48(TMP / 'sdk', source_assets, c48dir)
    pack_sdk(SOURCE / 'zx-ux-sdk', SOURCE / 'zx-ux', TMP,
             candidate / 'sdk/bin')
    require(verify_tape_and_compiled_pairs(target / 'ZX-UX.tap', c48dir) == n,
            'Selected file count mismatch')
    require(source_before == snapshot_inputs(), 'Builder changed source files')
    actual = sorted(str(p.relative_to(candidate)) for p in candidate.rglob('*') if p.is_file())
    require(all(p.startswith(('zx-ux/', 'sdk/bin/', 'assets/c48-bin/')) for p in actual),
            'Unexpected output file placement')
    expected_c48 = n * 2
    require(len([p for p in actual if p.startswith('assets/c48-bin/')]) == expected_c48,
            'Missing executable/tape pair from dist')
    # The completed candidate is only a provisional baseline, never a signed release.
    status = {'status': 'partial beta-0.0.7 development candidate',
              'program_count': n,
              'boot_transport': 'single-CODE TAP and compact turbo boot TZX; pending external release gates',
              'candidate_file_count': len(actual)}
    (RELEASE / 'manifest.json').write_text(json.dumps(status, indent=2) + '\n')
    old = TMP / 'dist-previous'
    if old.exists():
        shutil.rmtree(old)
    if DIST.exists():
        require(DIST.is_dir() and not DIST.is_symlink(), 'Unsafe previous distribution')
        DIST.rename(old)
    try:
        candidate.rename(DIST)
    except BaseException:
        if old.exists() and not DIST.exists():
            old.rename(DIST)
        raise
    # The promoted files alone are current. Do not retain duplicate older
    # distributions among intermediate build files after a successful build.
    if old.exists():
        shutil.rmtree(old)
    print('BETA-0.0.7 DEVELOPMENT CANDIDATE: %d C48 pairs and two boot transports; external gates still required' % n)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sjasm', default=shutil.which('sjasmplus'))
    args = p.parse_args()
    try:
        build(args.sjasm or '')
    except (OSError, RuntimeError, ValueError) as exc:
        print('BUILD FAILED; previous dist, if any, remains unchanged: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Capture C48 bytecode in the ZX-UX SDK host VM.

These images are generated from the same SSX files tested on the Spectrum.
They are NOT images from the separate upstream C48 reference compiler/VM.
Run after tools/mktapes.py, with SkoolKit 10.1 on PYTHONPATH:
    python3 -B tools/c48_proofs.py
Native emulator images are generated separately by tests/ssxrun.py.
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'sdk'))
import rvm

CASES = {'hello': [], 'fortune': [], 'city': ['2'], 'secforge': []}
OUTPUT = ROOT / 'build' / 'shots-vm'


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    info = []
    for name, args in CASES.items():
        source = ROOT / 'build' / 'c48' / (name + '.ssx')
        payload = source.read_bytes()
        vm = rvm.VM(payload, args, b'', None, 1234)
        reason = vm.run(1500)
        screen = vm.screen()
        if len(screen) != 6912:
            raise SystemExit('Invalid 48K screen size: ' + name)
        target = OUTPUT / (name + '.rvm.png')
        rvm.write_png(screen, str(target), vm.tr.border)
        if not target.is_file():
            raise SystemExit('Missing VM capture: ' + name)
        entry = {'name': name, 'runtime': 'ZX-UX SDK rvm',
                 'not_upstream_reference': True,
                 'program_sha256': hashlib.sha256(payload).hexdigest(),
                 'screen_sha256': hashlib.sha256(screen).hexdigest(),
                 'reason': reason, 'png': str(target.relative_to(ROOT))}
        info.append(entry)
        print(name, 'ZX-UX SDK rvm', reason, len(screen), 'bytes')
    (OUTPUT / 'results.json').write_text(json.dumps(info, indent=2) + '\n')


if __name__ == '__main__':
    main()

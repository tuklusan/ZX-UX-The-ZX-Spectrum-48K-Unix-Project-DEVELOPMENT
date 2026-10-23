"""Verify a dynamic VAL expression using an actual ZX-UX screen comparison."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys


def compile_basic(root, trial, name, source):
    listing = trial / (name+'.bas')
    binary = trial / (name+'.ssx')
    listing.write_text(source)
    cmd = [sys.executable, str(trial/'rbc'/'rbc.py'), str(listing),
           '--frontend', 'upstream-pyhsb', '--sdk', str(root/'src/zx-ux-sdk'),
           '--rom', str(root/'src/zx-ux-sdk/rom/48.rom'),
           '--tape', str(trial/'hisoft48.tap'), '-o', str(binary),
           '--report', str(trial/(name+'-report.json'))]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, timeout=100)
    if result.returncode or not binary.is_file():
        raise RuntimeError(name+' compiler error: '+result.stdout)
    return binary


def first_characters(root, binary):
    sys.path.insert(0, str(root/'dist/sdk/bin/py'))
    import rvm
    machine = rvm.run_kernel(str(binary), system=str(root/'dist/zx-ux/tzx/ZX-UX.tzx'), frames=160)
    bitmap, _border = machine.picture()
    if not (machine.fg and machine.fg.started is not None):
        raise RuntimeError('ZX-UX did not start '+binary.name)
    # In the Spectrum's interleaved 256x192 screen, each of the first 8
    # scanlines begins at row*256. Compare the exact glyph pixels, not OCR.
    return b''.join(bytes(bitmap[row*256:row*256+4]) for row in range(8))


def run(root: Path, trial: Path):
    expected = compile_basic(root, trial, 'val-reference',
        '10 PRINT AT 0,0;"PASS":GO TO 10\n')
    dynamic = compile_basic(root, trial, 'val-native-probe',
        '10 LET a$="3*4"\n'
        '20 LET n=VAL a$\n'
        '25 IF n=12 THEN GO TO 40\n'
        '30 PRINT AT 0,0;"FAIL":GO TO 30\n'
        '40 PRINT AT 0,0;"PASS":GO TO 40\n')
    ref_pixels = first_characters(root, expected)
    result_pixels = first_characters(root, dynamic)
    summary = {'reference_pixels':ref_pixels.hex(),
               'actual_pixels':result_pixels.hex(),
               'matched':ref_pixels==result_pixels,
               'reference_nonempty':any(ref_pixels)}
    (trial/'val-native-probe-result.json').write_text(json.dumps(summary,indent=2)+'\n')
    if not any(ref_pixels) or ref_pixels != result_pixels:
        raise RuntimeError('native ROM VAL screen mismatch: '+str(summary))
    print('native VAL 3*4 expression screen: PASS')


if __name__ == '__main__':
    if len(sys.argv)!=3:
        raise SystemExit('usage: val_native_probe.py PROJECT_ROOT TRIAL_DIR')
    run(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
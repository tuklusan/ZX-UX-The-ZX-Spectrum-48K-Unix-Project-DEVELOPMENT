"""Exercise runtime VAL on a real native ZX-UX program, not just compiler output."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys


def run(root: Path, trial: Path):
    source = trial / 'val-native-probe.bas'
    output = trial / 'val-native-probe.ssx'
    report = trial / 'val-native-probe-report.json'
    # The string contains an expression, not merely a decimal digit. The 48K
    # ROM's VAL implementation must evaluate 3*4 to 12 at native run time.
    source.write_text('10 LET a$="3*4"\n'
                      '20 LET n=VAL a$\n'
                      '30 IF n=12 THEN BORDER 2:GO TO 30\n'
                      '40 BORDER 4:GO TO 40\n')
    command = [sys.executable, str(trial/'rbc'/'rbc.py'), str(source),
               '--frontend', 'upstream-pyhsb', '--sdk', str(root/'src/zx-ux-sdk'),
               '--rom', str(root/'src/zx-ux-sdk/rom/48.rom'),
               '--tape', str(trial/'hisoft48.tap'), '-o', str(output),
               '--report', str(report)]
    result = subprocess.run(command, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=100)
    if result.returncode != 0 or not output.is_file():
        raise RuntimeError('native VAL fixture did not compile: ' + result.stdout)
    sys.path.insert(0, str(root/'dist/sdk/bin/py'))
    import rvm
    machine = rvm.run_kernel(str(output), system=str(root/'dist/zx-ux/tzx/ZX-UX.tzx'), frames=160)
    _bitmap, border = machine.picture()
    state = {'native_started': bool(machine.fg and machine.fg.started is not None),
             'why': machine.why, 'border': int(border), 'expected_border': 2}
    (trial/'val-native-probe-result.json').write_text(json.dumps(state,indent=2)+'\n')
    if not state['native_started'] or state['border'] != 2:
        raise RuntimeError('native ROM VAL did not produce expected expression result: '+str(state))
    print('native VAL 3*4 expression: PASS')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: val_native_probe.py PROJECT_ROOT TRIAL_DIR')
    run(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
"""Run the prepared RBC CLI end to end against the real HELLO BASIC input.

The frozen assembler and linker independently validate the emitted object.
The test creates output only in the experiment scratch directory.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def check(root: Path):
    rbc = root / 'trial-result/rbc/rbc.py'
    source = root / 'trial-result/hello.bas'
    sdk = root / 'src/zx-ux-sdk'
    original = source.read_bytes()
    sys.path.insert(0, str(sdk))
    import ras
    import rld

    common = [sys.executable, str(rbc), str(source),
              '--frontend', str(root / 'upstream-pyhsb'),
              '--sdk', str(sdk), '--rom', str(sdk / 'rom/48.rom'),
              '--tape', str(root / 'trial-result/hisoft48.tap')]

    def run(extra, expected=0):
        proc = subprocess.run(common + extra, capture_output=True, text=True)
        if proc.returncode != expected:
            raise AssertionError((extra, proc.returncode, proc.stdout, proc.stderr))
        return proc

    default = source.with_suffix('.ssx')
    assembly = source.with_suffix('.s')
    obj_path = source.with_suffix('.sso')
    report = source.with_suffix('.fit.json')
    for path in (default, assembly, obj_path, report):
        path.unlink(missing_ok=True)
    run(['--report', str(report)])
    result = rld.parse_ssx(default.read_bytes())
    info = json.loads(report.read_text())
    assert info['font_source'] == 'spectrum_rom'
    assert info['fit_default'] is True
    assert info['font_bytes'] == 0
    assert info['memory_required'] <= info['memory_limit']
    assert default.parent == source.parent

    run(['-S'])
    assert assembly.read_text().startswith('    section text\n')
    run(['-c'])
    obj = obj_path.read_bytes()
    assert obj.startswith(b'SSO1')
    restored, *_ = rld.link([rld.Obj(obj, 'hello')], [], 'start', result['stack'], 0)
    rebuilt = rld.parse_ssx(restored)
    for field in ('image', 'bss', 'stack', 'relocs'):
        assert rebuilt[field] == result[field], field

    private = source.with_suffix('.private.ssx')
    run(['--no-fit', '-o', str(private)])
    assert len(rld.parse_ssx(private.read_bytes())['image']) >= len(result['image']) + 768

    too_big = source.with_suffix('.oversize.ssx')
    failure = run(['--max', '1', '-o', str(too_big), '--report', str(report)], 1)
    assert '%RBC RBC_MEMORY_LIMIT Line: - Statement: -' in failure.stderr
    assert 'Executable requires ' in failure.stderr and 'native memory' in failure.stderr
    assert not too_big.exists()
    assert json.loads(report.read_text())['cause_category'] == 'native-memory-limit'

    unsupported = run(['--bytecode', '-o', str(too_big)], 2)
    assert 'unavailable' in unsupported.stderr
    assert not too_big.exists()
    assert source.read_bytes() == original
    outcome = {'status': 'pass', 'source': str(source.relative_to(root)),
               'default_output': str(default.relative_to(root)),
               'assembly_output': str(assembly.relative_to(root)),
               'object_output': str(obj_path.relative_to(root)),
               'rom_font_bytes_saved': 768,
               'default_native_memory': info['memory_required'],
               'default_limit': info['memory_limit'],
               'linkable_object': True, 'source_unchanged': True,
               'oversize_failure_checked': True,
               'unsupported_bytecode_rejected': True}
    (root / 'trial-result/rbc-cli-validation.json').write_text(json.dumps(outcome, indent=2)+'\n')
    print('CHECK native RBC CLI and fitting PASS')


if __name__ == '__main__':
    check(Path(__file__).resolve().parents[3])

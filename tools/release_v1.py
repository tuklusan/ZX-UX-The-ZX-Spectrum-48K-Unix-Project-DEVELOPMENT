#!/usr/bin/env python3
"""Run the external beta checks; the portable builder needs no test tools."""
import argparse, shlex, subprocess, sys
from importlib.util import find_spec
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ('sjasm', 'tap2sna', 'fuse-test-command'):
        p.add_argument('--' + flag, required=True)
    a = p.parse_args()
    r = Path(__file__).resolve().parent.parent
    w = r / 'tests/.work'; w.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    skoolkit = find_spec('skoolkit')
    if not skoolkit: p.error('SkoolKit test tools are not available')
    c48, ix, env = (str(w / n) for n in ('c48.json', 'ix.json', 'env1.json'))
    commands = ([py, '-B', 'release/build/build.py', '--sjasm', a.sjasm],
                [py, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'release_*checks.py'],
                [py, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*beta7.py'],
                [py, '-B', 'tests/c48/conformance.py', '--backend', 'both', '--report', c48],
                [py, '-B', 'tests/c48/ix_frame_probe.py', '--report', ix],
                [py, '-B', 'tests/c48/native_env1_v1.py', '--tap2sna', a.tap2sna, '--report', env],
                [py, '-B', 'tests/c48/coverage_gate.py', '--report', c48, '--ix-proof', ix, '--env1-proof', env],
                [py, '-B', 'tests/c48/target_gate.py', '--report', c48, '--ix-proof', ix, '--env1-proof', env],
                [py, '-B', 'tests/run_migrated_baseline.py', '--tap2sna', a.tap2sna,
                 '--skoolkit', str(Path(skoolkit.origin).resolve().parents[1])],
                shlex.split(a.fuse_test_command))
    for command in commands:
        subprocess.run(command, cwd=r, check=True)
    print('Local release checks passed; publishing is a separate gate.')

if __name__ == '__main__':
    main()

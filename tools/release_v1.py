#!/usr/bin/env python3
"""Build, test, scan, and assemble a ZX-UX v1 release.

Start from a clean committed checkout. All tools and the private checker
must live outside the checkout. Nothing is copied to release/ unless
all required build and emulator tests have passed.

Usage:
  python3 tools/release_v1.py --checker /private/checker.py \
      --sjasm /tools/sjasmplus \
      --tap2sna /tools/tap2sna.py \
      --fuse-test-command '/path/to/checked-fuse-boot-test'

The independent FUSE boot test is mandatory. Its command must return
zero on success and must not require interaction.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / 'build'
RELEASE = ROOT / 'release'
PYTHON = sys.executable


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def run(cmd, checker=None, env=None, log=None):
    """Scan a complete command before running it. Save its real output."""
    command = shlex.join([str(arg) for arg in cmd])
    if checker:
        scan = subprocess.run([PYTHON, str(checker), 'check', '--command', command],
                              cwd=ROOT, capture_output=True, text=True)
        require(scan.returncode == 0, 'Private checker refused a command')
    result = subprocess.run([str(arg) for arg in cmd], cwd=ROOT,
                            env=env, capture_output=True, text=True)
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text('Command: ' + command + '\nExit: ' +
                       str(result.returncode) + '\n\n' +
                       result.stdout + '\n' + result.stderr)
    require(result.returncode == 0,
            'Command failed; inspect ' + str(log if log else command))
    return result.stdout + result.stderr


def check(checker, flag, name):
    result = subprocess.run([PYTHON, str(checker), 'check', flag, str(name)],
                            cwd=ROOT, capture_output=True, text=True)
    require(result.returncode == 0,
            'Private checker rejected input; do not distribute it')


def check_tracked_sources(checker, after_build=False):
    """Check only Git-indexed project files, never .git or untracked caches.

    All tracked paths must exist and have the bytes recorded by the index.
    Generated outputs receive their own validation before delivery.
    """
    records = subprocess.check_output(['git', 'ls-files', '-s', '-z'], cwd=ROOT)
    require(bool(records), 'No tracked project files')
    for record in records.split(b'\0'):
        if not record:
            continue
        descriptor, raw_path = record.split(b'\t', 1)
        mode, expected, stage = descriptor.split(b' ')
        require(stage == b'0', 'Unmerged Git index')
        relative = Path(os.fsdecode(raw_path))
        require(not relative.is_absolute() and '..' not in relative.parts,
                'Unsafe Git path')
        path = ROOT / relative
        require(path.is_file() and not path.is_symlink(),
                'Tracked file missing or unsupported')
        actual = subprocess.check_output(['git', 'hash-object', '--', str(relative)],
                                         cwd=ROOT).strip()
        if not (after_build and relative.parts[0] == 'build'):
            require(actual == expected, 'Tracked file differs from Git index')
        check(checker, '--file', path)


def version_data(sjasm):
    text = run([sjasm, '--version'])
    return text.strip().splitlines()[0]


def count_log(log):
    text = log.read_text()
    passed = len(re.findall(r'\bPASS\b', text))
    failed = len(re.findall(r'\bFAIL\b', text))
    return passed, failed


def screenshot_check(checker):
    config = json.loads((ROOT / 'sdk/tests/runs.json').read_text())
    for name, entry in config.items():
        name = name.replace(':', '_')
        if entry.get('ZX-UX') != 'skip':
            require((BUILD / 'shots' / (name + '.ZX-UX.png')).is_file(),
                    'Missing emulator image for ' + name)
        require((BUILD / 'shots-vm' / (name + '.png')).is_file(),
                'Missing C48 VM image for ' + name)
    require((BUILD / 'ZX-UX-multitask.png').is_file(),
            'Missing Hanoi + Queens8 emulator capture')
    for d in (BUILD / 'shots', BUILD / 'shots-vm'):
        for img in d.glob('*.png'):
            check(checker, '--file', img)
    check(checker, '--file', BUILD / 'ZX-UX-multitask.png')


def manifest(commit, versions, logs):
    parts = ['ZX-UX v1 release manifest', '', 'Source commit: ' + commit,
             'Assembler: ' + versions['assembler'],
             'SkoolKit: ' + versions['skoolkit'],
             'Tests:']
    for key, log in logs.items():
        p, f = count_log(log)
        parts.append('  %s: PASS=%d FAIL=%d exit=0' % (key, p, f))
    parts.extend(['', 'Files (SHA-256 and byte size):'])
    for file in sorted(RELEASE.rglob('*')):
        if not file.is_file() or file.name == 'manifest.txt':
            continue
        parts.append('%s  %d  %s' % (hashlib.sha256(file.read_bytes()).hexdigest(),
                                    file.stat().st_size, file.relative_to(RELEASE)))
    (RELEASE / 'manifest.txt').write_text('\n'.join(parts) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checker', required=True, type=Path)
    parser.add_argument('--sjasm', required=True, type=Path)
    parser.add_argument('--tap2sna', required=True, type=Path)
    parser.add_argument('--fuse-test-command', required=True)
    args = parser.parse_args()
    checker = args.checker.resolve()
    sjasm = args.sjasm.resolve()
    corpus = ROOT / 'programs' / 'c48'
    tape_tool = args.tap2sna.resolve()
    for tool in (checker, sjasm, tape_tool):
        require(tool.is_file() and not tool.is_symlink(), 'Missing checked tool')
        require(ROOT not in tool.parents, 'Private tools must stay outside Git')
    require((corpus / 'demos/hanoi.c').is_file() and
            (corpus / 'demos/queens8.c').is_file() and
            (corpus / 'ailmzx48/ailmzx48.c').is_file(),
            'Checked-in v1 C48 sources or LM source are missing')
    require(not RELEASE.exists(), 'Remove or archive the old release first')
    require(not run(['git', 'status', '--porcelain']).strip(),
            'Release must start from a clean checkout')
    commit = run(['git', 'rev-parse', 'HEAD']).strip()
    run([PYTHON, checker, 'self-test'])
    check(checker, '--file', sjasm)
    check(checker, '--file', tape_tool)
    check_tracked_sources(checker)
    spec = importlib.util.find_spec('skoolkit')
    require(spec is not None and spec.origin is not None,
            'SkoolKit 10.1 is not installed')
    # Third-party simulator binaries are outside the project-text scan.
    # Verify these exact owner-supplied toolbox bytes instead.
    import skoolkit
    import skoolkit.csimulator
    require(skoolkit.CSimulator is not None and Path(skoolkit.ROM48).is_file(),
            'SkoolKit emulator and its 48K ROM are unavailable')
    require(skoolkit.VERSION == '10.1', 'Requires SkoolKit 10.1')
    toolbox = sjasm.parent.parent
    require(Path(spec.origin).resolve() ==
            (toolbox / 'runtime/skoolkit/__init__.py').resolve(),
            'SkoolKit was not loaded from the checked toolbox')
    sim_path = Path(skoolkit.csimulator.__file__).resolve()
    require(sim_path.parent == Path(spec.origin).resolve().parent,
            'Compiled simulator does not belong to the checked toolbox')
    for path, expected in (
        (sjasm, '2aafd9bbc62c4ff90b6c69aa71a94a33afda395b587c2936c5fedb970e67adc0'),
        (Path(skoolkit.ROM48), 'd55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42'),
        (sim_path, '2116a3d1416bb273be4ef686797a9e055cfbc3217be337ecb878f07f093601b2'),
    ):
        require(path.is_file() and not path.is_symlink() and
                hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                'Checked toolbox file hash does not match')
    from PIL import Image  # Required for real image generation and inspection.
    require(Image is not None, 'Pillow is missing')
    sj_version = version_data(str(sjasm))
    logs = {}

    def step(name, command, env=None):
        log = BUILD / 'logs' / (name + '.txt')
        run(command, checker=checker, env=env, log=log)
        logs[name] = log
        check(checker, '--file', log)

    step('release-self-tests', [PYTHON, '-B', '-m', 'unittest', 'discover',
                                '-s', 'tests', '-p', 'release_*checks.py', '-v'])
    step('build', [PYTHON, '-B', 'tools/build.py', str(sjasm)])
    for name in ('unix.bin', 'fs.img', 'ZX-UX.tap', 'ZX-UX.tzx'):
        check(checker, '--file', BUILD / name)
    step('boot-image-static', [PYTHON, '-B', 'tests/test_boot_v1.py'])
    step('c48-runtime', [PYTHON, '-B', 'sdk/lib/build.py'])
    step('c48-abi-ix', [PYTHON, '-B', 'tests/c48/ix_abi_probe.py',
                        '--report', str(BUILD / 'logs/ix-abi-proof.json')])
    check(checker, '--file', BUILD / 'logs/ix-abi-proof.json')
    step('c48-language', [PYTHON, '-B', 'tests/c48/conformance.py',
                          '--backend', 'both', '--report',
                          str(BUILD / 'logs' / 'c48-conformance.json')])
    step('c48-coverage', [PYTHON, '-B', 'tests/c48/coverage_gate.py',
                          '--report', str(BUILD / 'logs' / 'c48-conformance.json')])
    step('assembler-comparison', [PYTHON, '-B', 'sdk/tests/test_ras.py'],
         {**os.environ, 'SJASMPLUS': str(sjasm)})
    step('rom-tape-boot', [PYTHON, '-B', str(tape_tool),
                           'build/ZX-UX.tzx', 'build/test.z80'])
    step('system-regression', [PYTHON, '-B', 'tests/suite.py'])
    step('c48-program-tapes', [PYTHON, '-B', 'tools/mktapes.py'])
    step('c48-emulator', [PYTHON, '-B', 'tests/ssxrun.py', '--png',
                          str(BUILD / 'shots')])
    step('c48-v1-native', [PYTHON, '-B', 'sdk/tests/oracle.py',
                           '--native', '--png', str(BUILD / 'shots-vm')])
    step('c48-v1-bytecode', [PYTHON, '-B', 'sdk/tests/oracle.py',
                             '--bytecode', '--png', str(BUILD / 'shots-vm')])
    step('lm-new-sdk', [PYTHON, '-B', 'tools/lm_v1.py'])
    step('hanoi-queens8', [PYTHON, '-B', 'tools/mtsnap.py'])
    step('gallery', [PYTHON, '-B', 'tools/gallery.py',
                     str(logs['c48-emulator']), str(logs['c48-v1-bytecode'])])
    from fuse_release_gate import validate_boot_command, validate_boot_proof
    fuse_command, proof_paths = validate_boot_command(
        args.fuse_test_command, ROOT, BUILD, PYTHON)
    step('fuse-independent-boot', fuse_command)
    validate_boot_proof(proof_paths,
                        lambda path: check(checker, '--file', path))
    screenshot_check(checker)
    check_tracked_sources(checker, after_build=True)
    doc = ['ZX-UX UNIX v1 for the ZX Spectrum 48K',
           'This release was built from Git commit ' + commit + '.',
           'All required emulator and C48 tests completed without errors.',
           'The manifest has the exact checks and SHA-256 sums.',
           'Load ZX-UX.tzx or ZX-UX.tap through the Spectrum tape loader.',
           'Log in with any user name of 1 to 8 characters.',
           'Project, font, and third-party ROM terms are recorded in LICENSE.',
           'FUSE: independent boot checked']
    (BUILD / 'README.txt').write_text('\n'.join(doc) + '\n')
    check(checker, '--file', BUILD / 'README.txt')
    check(checker, '--tree', BUILD)
    step('release-copy', [PYTHON, '-B', 'tools/mkrelease.py', str(BUILD / 'logs')])
    shutil.copyfile(logs['release-copy'], RELEASE / 'logs/release-copy.txt')
    for extra in ('unix.bin', 'fs.img'):
        shutil.copyfile(BUILD / extra, RELEASE / extra)
    check(checker, '--tree', RELEASE)
    manifest(commit, {'assembler': sj_version, 'skoolkit': skoolkit.VERSION}, logs)
    check(checker, '--tree', RELEASE)
    print('Verified release:', RELEASE)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        print('RELEASE STOPPED:', exc, file=sys.stderr)
        sys.exit(1)

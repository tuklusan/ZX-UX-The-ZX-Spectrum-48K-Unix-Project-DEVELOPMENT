"""Enforce a real FUSE login proof for a freshly built ZX-UX release.

This is a release gate, not an emulator replacement. The independent
verification must execute tests/fuse_boot.py against build/ZX-UX.tzx.
"""
import hashlib
import json
from pathlib import Path
import shlex
import shutil

ROM_SHA256 = 'd55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42'
REQUIRED = ('--fuse', '--rom', '--tape', '--assets', '--libdir', '--screen')
ALLOWED = frozenset(REQUIRED + ('--wait', '--expect-zxux-login'))


def _require(ok, message):
    if not ok:
        raise RuntimeError(message)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_boot_command(command, root, build, python_executable):
    """Return argv and proof locations or reject unrelated shell commands."""
    root, build = Path(root).resolve(), Path(build).resolve()
    argv = shlex.split(command)
    _require(len(argv) >= 2, 'Missing FUSE verification command')
    program = shutil.which(argv[0]) or argv[0]
    _require(Path(program).resolve() == Path(python_executable).resolve(),
             'FUSE verification must use this Python executable')
    pos = 1
    if argv[pos] == '-B':
        pos += 1
    _require(pos < len(argv), 'Missing independent FUSE boot verifier')
    _require((root / argv[pos]).resolve() == root / 'tests/fuse_boot.py',
             'FUSE command must run tests/fuse_boot.py')
    args = argv[pos + 1:]
    flags = {}
    i = 0
    while i < len(args):
        flag = args[i]
        _require(flag in ALLOWED and flag not in flags,
                 'Unsupported or duplicate FUSE verifier option')
        if flag == '--expect-zxux-login':
            flags[flag] = True
            i += 1
        else:
            _require(i + 1 < len(args) and not args[i + 1].startswith('--'),
                     'Missing FUSE verifier option value')
            flags[flag] = args[i + 1]
            i += 2
    _require(all(k in flags for k in REQUIRED), 'FUSE verifier options missing')
    _require(flags.get('--expect-zxux-login') is True,
             'Release requires verified ZX-UX login screen')
    tape = (root / flags['--tape']).resolve()
    screen = (root / flags['--screen']).resolve()
    rom = (root / flags['--rom']).resolve()
    _require(tape == build / 'ZX-UX.tzx',
             'FUSE test must load the newly built build/ZX-UX.tzx')
    _require(screen.suffix.lower() == '.png' and screen != build and build in screen.parents,
             'FUSE capture must be a PNG in build/')
    _require(screen != tape and rom != tape, 'FUSE verifier inputs overlap')
    if '--wait' in flags:
        try:
            wait = int(flags['--wait'])
        except ValueError as error:
            raise RuntimeError('Invalid FUSE wait') from error
        _require(3 <= wait <= 120, 'Invalid FUSE wait')
    return argv, {'tape': tape, 'rom': rom, 'screen': screen,
                  'json': screen.with_suffix('.json')}


def validate_boot_proof(paths, check_file):
    """Verify the FUSE script captured this tape and an authentic screen."""
    tape, rom, screen, proof_path = (Path(paths[k]) for k in
                                     ('tape', 'rom', 'screen', 'json'))
    for file in (tape, rom, screen, proof_path):
        _require(file.is_file() and not file.is_symlink(),
                 'Required FUSE proof input is missing or linked')
    _require(rom.stat().st_size == 16384 and _sha(rom) == ROM_SHA256,
             'FUSE 48K ROM identity mismatch')
    _require(screen.stat().st_size > 0, 'Empty FUSE login capture')
    check_file(screen)
    check_file(proof_path)
    try:
        p = json.loads(proof_path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError) as error:
        raise RuntimeError('Invalid FUSE proof JSON') from error
    _require(p.get('result') == 'PASS' and p.get('machine') == 'ZX Spectrum 48K',
             'FUSE machine boot not confirmed')
    _require(p.get('expected_text') == 'ZX-UX login' and
             p.get('match_method') == 'checked ZX-UX login screen markers',
             'FUSE screen confirmation incomplete')
    for label, file in (('tape_sha256', tape), ('rom_sha256', rom),
                        ('screen_sha256', screen)):
        _require(p.get(label) == _sha(file), 'FUSE proof hash mismatch')
    marks = p.get('text_position')
    _require(isinstance(marks, dict) and
             all(isinstance(marks.get(k), list) and len(marks[k]) == 2 and
                 all(isinstance(v, int) for v in marks[k])
                 for k in ('boot_banner', 'console_title', 'login_prompt')),
             'FUSE login marker locations missing')
    return p

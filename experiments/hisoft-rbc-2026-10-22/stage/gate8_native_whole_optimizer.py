"""Audited whole-source upeepz80 *candidate* and native link, not gameplay proof.

The optimizer receives the entire original-source-typed assembly, including
protected data, runtime mnemonics, relocation words and BSS. No disassembled
binary, db/dw post-link dump or compiler fragment hook may supply its input.
A candidate is never granted runtime-equivalence or publication by this gate.
"""
from __future__ import annotations

import hashlib
import importlib
import inspect
from pathlib import Path
import sys

import ras
import rld
from symbolic_z80 import _check_optimizer_output, _check_protected, SymbolicError
from upeepz80_codegen import UPSTREAM_REVISION

# Blob identities read independently from the locked GitHub upstream commit.
_LOCKED = {
    '__init__.py': 'd5bf9e1ca2f80d671c09231520af1470cb7a185e',
    'peephole.py': '067ac45ed935fbe90f9e24a864cdf2eca163cc4c',
    'z80.py': '550b14e167a4a265aada5901d86e506225a9a1b9',
}
_LOCKED_REVISION = 'a48d725704b132c3ff23ac77232a3a412b56b15f'


class WholeOptimizerError(ValueError):
    """Cannot prove that the optimizer candidate is source-owned and safe."""


def _git_blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def load_locked_optimizer(root: Path):
    """Require fixed-source identity before importing upstream optimizer."""
    root = Path(root).resolve()
    if UPSTREAM_REVISION != _LOCKED_REVISION:
        raise WholeOptimizerError('upstream optimizer revision is not locked')
    for name, sha in _LOCKED.items():
        path = root / 'upeepz80' / name
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise WholeOptimizerError('locked optimizer source unavailable') from exc
        if _git_blob(raw) != sha:
            raise WholeOptimizerError('locked optimizer source identity differs: ' + name)
    old = sys.modules.get('upeepz80')
    old_file = Path(inspect.getfile(old)).resolve() if old is not None else None
    if old_file is not None and old_file != (root / 'upeepz80' / '__init__.py'):
        raise WholeOptimizerError('another upstream optimizer is already imported')
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    mod = importlib.import_module('upeepz80')
    from upeepz80 import peephole, z80
    if any(Path(inspect.getfile(obj)).resolve() != root / 'upeepz80' / path
           for obj, path in ((mod, '__init__.py'), (peephole, 'peephole.py'),
                             (z80, 'z80.py'))):
        raise WholeOptimizerError('optimizer imported from an unverified source path')
    return mod.PeepholeOptimizer()


def verify_whole_optimizer_candidate(assembly: str, native_baseline: bytes,
                                     optimizer, *, max_memory: int = 12000,
                                     expected_runtime_bytes: bytes | None = None):
    """Optimize the entire source once; prove native link and protected resources.

    Native byte changes alone cannot establish process behavior equivalence:
    shortened branches also move addresses, and numerical pointers and
    indirect edges remain unverified. Always return non-admitted status.
    """
    if not isinstance(assembly, str) or not assembly or not callable(optimizer):
        raise WholeOptimizerError('typed whole source and optimizer required')
    try:
        plain = rld.parse_ssx(native_baseline)
        # The source itself must independently rebuild the claimed baseline.
        # Merely relinking the optimizer output against an unrelated SSX lets
        # missing or substituted compiler source pass a native-link gate.
        baseline_obj = ras.assemble_text(assembly, 'rbc-whole-original.s')
        rebuilt, *_ = rld.link(
            [rld.Obj(baseline_obj, 'rbc-whole-original.sso')], [],
            entry='start', stack=plain['stack'])
        if rebuilt != native_baseline:
            raise WholeOptimizerError('whole source does not reproduce native baseline')
        candidate_text = optimizer(assembly)
        if not isinstance(candidate_text, str):
            raise WholeOptimizerError('optimizer did not return assembly text')
        _check_optimizer_output(candidate_text)
        _check_protected(assembly, candidate_text, {'start'})
        obj = ras.assemble_text(candidate_text, 'rbc-whole-upeepz80.s')
        candidate_ssx, *_ = rld.link(
            [rld.Obj(obj, 'rbc-whole-upeepz80.sso')], [],
            entry='start', stack=plain['stack'])
        linked = rld.parse_ssx(candidate_ssx)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError,
            SymbolicError, ras.AsmError, rld.LinkError) as exc:
        raise WholeOptimizerError('full-source optimizer candidate rejected: ' + str(exc)) from exc
    if (linked['entry'] != plain['entry'] or
            linked['bss'] != plain['bss'] or linked['stack'] != plain['stack']):
        raise WholeOptimizerError('optimizer changed native entry or BSS/stack allocation')
    baseline_total = len(plain['image']) + plain['bss'] + plain['stack']
    candidate_total = len(linked['image']) + linked['bss'] + linked['stack']
    candidate_memory = max(len(candidate_ssx), candidate_total)
    unchanged = candidate_ssx == native_baseline
    if unchanged and linked['image'] != plain['image']:
        raise WholeOptimizerError('candidate binary consistency check failed')
    if expected_runtime_bytes is not None and unchanged and (
            expected_runtime_bytes not in plain['image']):
        raise WholeOptimizerError('verified runtime resource differs from baseline')
    return {
        'locked_upstream_revision': _LOCKED_REVISION,
        'optimizer_full_program_source_presented': True,
        'native_baseline_sha256': hashlib.sha256(native_baseline).hexdigest(),
        'native_candidate_sha256': hashlib.sha256(candidate_ssx).hexdigest(),
        'native_baseline_source_reassembled': True,
        'native_candidate_link_verified': True,
        'protected_source_lines_preserved': True,
        'candidate_byte_identical': unchanged,
        'native_baseline_file_bytes': len(native_baseline),
        'native_candidate_file_bytes': len(candidate_ssx),
        'native_baseline_image_bytes': len(plain['image']),
        'native_candidate_image_bytes': len(linked['image']),
        'native_baseline_total_bytes': baseline_total,
        'native_candidate_total_bytes': candidate_total,
        'native_baseline_relocations': len(plain['relocs']),
        'native_candidate_relocations': len(linked['relocs']),
        'candidate_file_bytes_saved': len(native_baseline) - len(candidate_ssx),
        'candidate_total_bytes_saved': baseline_total - candidate_total,
        'candidate_within_default_limit': candidate_memory <= max_memory,
        'optimizer_candidate_admitted_for_publication': False,
        'native_behavior_verified': False,
        'full_program_optimized': False,
    }

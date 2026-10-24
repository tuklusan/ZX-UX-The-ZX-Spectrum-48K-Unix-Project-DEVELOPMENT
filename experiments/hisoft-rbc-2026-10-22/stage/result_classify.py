"""Assign one stable cause to a failed original-BASIC compiler input.

The caller keeps the complete compiler output. This module only groups it
so repeated faults can be investigated together without losing details.
"""
from __future__ import annotations

import re


def classify(output: str) -> str:
    """Classify a real compiler failure without turning it into success."""
    text = output.lower()
    standardized = re.search(r'^%RBC ([A-Z]+_[A-Z0-9_]+) Line:', output, re.M)
    if standardized:
        code = standardized.group(1)
        if code == 'RBC_MEMORY_LIMIT':
            return 'native-memory-limit'
        if code == 'RBC_TZX_CONVERSION':
            return 'TZX conversion'
        if code == 'RBC_TZX_FIDELITY':
            return 'BAS/TZX semantic difference'
        if code == 'RBC_SSX_DIFFERENCE':
            return 'linked-binary-mismatch'
        if code.startswith('BAS_'):
            return 'source-parse'
        if code.startswith('ROM_'):
            return 'spectrum-rom-syntax'
        if code.startswith('HIS_'):
            return 'hisoft-compiler'
        if code.startswith('RBC_TAPE_'):
            return 'external-io'
        if code.startswith('RBC_USR_'):
            return 'machine-code-usr'
        if code.startswith(('RBC_NATIVE_', 'RBC_COMPILER_')):
            return 'compiler-error'
        if code in ('RBC_PROTECTED_WRITE', 'RBC_PROTECTED_READ',
                    'RBC_MEMORY_POLICY', 'RBC_UDG_RANGE'):
            return 'memory-other'
        return 'compiler-error'
    if 'zx-ux memory check stopped' in text:
        match = re.search(r'\b(?:poke|peek|load|out|usr)\s+([a-z_]+)', text)
        operation = match.group(1) if match else ''
        classes = {
            'global_memory_write': 'memory-global-write',
            'unbounded_memory_write': 'memory-unbounded-write',
            'global_memory_read': 'memory-global-read',
            'tape_or_external_io': 'external-io',
        }
        return classes.get(operation, 'memory-other')
    if re.search(r'needs \d+ bytes of native memory \(limit \d+\)', text):
        return 'native-memory-limit'
    if 'no spectrum character for' in text:
        return 'character-encoding'
    if 'computed line number' in text:
        return 'computed-line'
    if 'dim again, with different sizes' in text:
        return 'array-redimension'
    if 'expecting a number line' in text:
        return 'numeric-expression'
    if 'not supported line' in text:
        return 'unsupported-basic'
    if 'invalid basic text line' in text or 'sourceerror' in text:
        return 'source-parse'
    if 'traceback' in text:
        return 'compiler-exception'
    return 'compiler-error'

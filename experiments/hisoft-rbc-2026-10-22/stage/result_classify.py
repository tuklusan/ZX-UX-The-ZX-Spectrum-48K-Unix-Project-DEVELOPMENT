"""Assign one stable cause to a failed original-BASIC compiler input.

The caller keeps the complete compiler output. This module only groups it
so repeated faults can be investigated together without losing details.
"""
from __future__ import annotations

import re


def classify(output: str) -> str:
    """Classify a real compiler failure without turning it into success."""
    text = output.lower()
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

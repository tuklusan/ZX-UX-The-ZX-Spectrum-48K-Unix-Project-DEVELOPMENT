"""Strictly recognize original 48K keyboard control byte writes.

Only literal values used by the archived games are admitted. These two ROM
variables are preserved around execution by startup_colors; all other
protected addresses and computed writes remain blocked.
"""
from __future__ import annotations
import re

_CONTROLS = {23658: {0, 9, 10, 255}, 23609: {110, 111}}
_ASSIGNMENT = re.compile(r"^\s*(23658|23609)\s*,\s*(-?[0-9]+)\s*$")


def allow_rom_keyboard_controls(findings):
    changed = 0
    for item in findings:
        if not (item.operation == "POKE" and
                item.classification == "global_memory_write" and
                item.severity == "block"):
            continue
        match = _ASSIGNMENT.fullmatch(item.expression)
        if not match:
            continue
        address, value = int(match[1]), int(match[2])
        if value not in _CONTROLS[address]:
            continue
        item.severity = "info"
        item.classification = "rom_keyboard_control"
        changed += 1
    return changed

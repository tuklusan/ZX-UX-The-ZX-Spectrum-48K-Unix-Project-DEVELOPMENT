"""Post-codegen upeepz80 integration for authentic native RBC SSX output.

Current RBC's -S output is a lossless db/dw rendering of an already linked
image, not mnemonic instruction IR. Preserve all relocation and binary
semantics: a peephole change is accepted only when the relinked SSX is exactly
the original. Any proposed changing executable requires a future labelled
mnemonic backend and separate control-flow/relocation proof.
"""
from __future__ import annotations

import hashlib

from rbc_output import asm_from_ssx, memory_required

UPSTREAM_REVISION = "a48d725704b132c3ff23ac77232a3a412b56b15f"


def optimize_ssx(payload: bytes, rld, ras=None, optimizer=None):
    """Chain an independently installed upeepz80 over final output assembly.

    Return (verified linked SSX, measurements). Fail closed on changed bytes:
    the current assembler emission uses fixed numeric offsets for relocations.
    """
    if ras is None:
        import ras as ras
    if optimizer is None:
        from upeepz80 import PeepholeOptimizer
        optimizer = PeepholeOptimizer()
    original = rld.parse_ssx(payload)
    source = asm_from_ssx(original)
    optimized = optimizer.optimize(source)
    if not isinstance(optimized, str):
        raise TypeError("upeepz80 did not return assembly text")
    obj = ras.assemble_text(optimized, "rbc-upeepz80.s")
    linked, *_ = rld.link(
        [rld.Obj(obj, "rbc-upeepz80")], [], "start",
        stack=original["stack"], heap=original["heap"], flags=original["flags"]
    )
    checked = rld.parse_ssx(linked)
    if linked != payload:
        # No guessing about moved machine-code instruction addresses or
        # POKE/USR offsets. Source-level mnemonic IR is needed for changes.
        raise ValueError(
            "upeepz80 changed linked bytes; cannot prove native instruction "
            "addresses and relocations with db/dw-only output"
        )
    result = {
        "upstream_revision": UPSTREAM_REVISION,
        "input_sha256": hashlib.sha256(payload).hexdigest(),
        "linked_sha256": hashlib.sha256(linked).hexdigest(),
        "input_file_bytes": len(payload),
        "linked_file_bytes": len(linked),
        "input_image_bytes": len(original["image"]),
        "linked_image_bytes": len(checked["image"]),
        "bss_bytes": original["bss"],
        "stack_bytes": original["stack"],
        "input_memory_required": memory_required(original, len(payload)),
        "linked_memory_required": memory_required(checked, len(linked)),
        "saved_file_bytes": len(payload) - len(linked),
        "saved_memory_bytes": memory_required(original, len(payload))
                              - memory_required(checked, len(linked)),
        "assembly_was_changed": source != optimized,
        "stats": dict(getattr(optimizer, "stats", {})),
        "backend": "ssx-db-dw-roundtrip",
    }
    return linked, result

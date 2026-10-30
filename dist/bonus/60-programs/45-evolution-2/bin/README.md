# 45-evolution-2 — Native RBC result

Original BASIC and tokenized tape were kept unchanged.
- Independent TZX conversion: passed, 105 BASIC lines.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=13932, image=12456, bss=1677, stack=384, total=14517, max=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=13932, image=12456, bss=1677, stack=384, total=14517, max=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

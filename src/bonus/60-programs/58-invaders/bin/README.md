# 58-invaders — Native RBC result

Original BASIC and tokenized tape were kept unchanged.
- Independent TZX conversion: passed, 90 BASIC lines.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: ZX-UX INPUT memory limit exceeded: file=14340, image=12735, bss=2980, stack=384, total=16099, max=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: ZX-UX INPUT memory limit exceeded: file=14340, image=12735, bss=2980, stack=384, total=16099, max=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

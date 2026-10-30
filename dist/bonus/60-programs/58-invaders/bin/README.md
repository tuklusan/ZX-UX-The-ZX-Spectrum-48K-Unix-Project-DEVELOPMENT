# 58-invaders — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `ced3897dce16a21d555ad4bc6e26b63a36ae4028fe36ce44dabd4cb85349d6f5`
- TZX SHA-256: `2332416e06e6387faabe7cc587731e1eb003255e0bf933d12fdad8902f5157d7`
- Independent TZX conversion: passed, 90 BASIC lines; decoded SHA-256 `ced3897dce16a21d555ad4bc6e26b63a36ae4028fe36ce44dabd4cb85349d6f5`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: ZX-UX INPUT memory limit exceeded: file=14340, image=12735, bss=2980, stack=384, total=16099, max=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: ZX-UX INPUT memory limit exceeded: file=14340, image=12735, bss=2980, stack=384, total=16099, max=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

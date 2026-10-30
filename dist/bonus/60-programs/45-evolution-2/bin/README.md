# 45-evolution-2 — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `45d973e81270c9218c1a8a60ad5e69199134dfdde69507f069abc9147e8f2efc`
- TZX SHA-256: `623bc16f3749769f045e82f9f8f4369eaf18afacbeebd9f1fabad87a04409bf1`
- Independent TZX conversion: passed, 105 BASIC lines; decoded SHA-256 `45d973e81270c9218c1a8a60ad5e69199134dfdde69507f069abc9147e8f2efc`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=13932, image=12456, bss=1677, stack=384, total=14517, max=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=13932, image=12456, bss=1677, stack=384, total=14517, max=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

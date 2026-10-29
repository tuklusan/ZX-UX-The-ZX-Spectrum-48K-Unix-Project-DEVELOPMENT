# 45-evolution-2 — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `45d973e81270c9218c1a8a60ad5e69199134dfdde69507f069abc9147e8f2efc`
- TZX SHA-256: `623bc16f3749769f045e82f9f8f4369eaf18afacbeebd9f1fabad87a04409bf1`
- Independent TZX conversion: passed, 105 BASIC lines; decoded SHA-256 `45d973e81270c9218c1a8a60ad5e69199134dfdde69507f069abc9147e8f2efc`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED UnsupportedTapeOperation: RBC E_TAPE_UNSUPPORTED: Line 1860: LOAD requires external tape I/O; RBC supports standalone BASIC programs only`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED UnsupportedTapeOperation: RBC E_TAPE_UNSUPPORTED: Line 1860: LOAD requires external tape I/O; RBC supports standalone BASIC programs only`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

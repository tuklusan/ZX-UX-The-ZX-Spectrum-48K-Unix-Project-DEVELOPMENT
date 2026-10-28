The game requires tape LOAD, which this native compiler cannot safely support.

Original BASIC: `45-evolution-2.bas`; SHA-256: `45d973e81270c9218c1a8a60ad5e69199134dfdde69507f069abc9147e8f2efc`.

Original tape: `45-evolution-2.tzx`; SHA-256: `623bc16f3749769f045e82f9f8f4369eaf18afacbeebd9f1fabad87a04409bf1`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED UnsupportedTapeOperation: RBC E_TAPE_UNSUPPORTED: Line 1860: LOAD requires external tape I/O; RBC supports standalone BASIC programs only`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED UnsupportedTapeOperation: RBC E_TAPE_UNSUPPORTED: Line 1860: LOAD requires external tape I/O; RBC supports standalone BASIC programs only`

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

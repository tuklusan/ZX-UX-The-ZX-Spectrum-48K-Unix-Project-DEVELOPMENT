# 44-evolution-1 — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `51a25b292da65e4dfce032bfb0d778c0364a31f2d779e8c989de54aebabb2675`
- TZX SHA-256: `8e72b017a3cd647829f84fbecdb4b8e26a3bc08b20da66ffb8ebaecd91ed14fb`
- Independent TZX conversion: passed, 108 BASIC lines; decoded SHA-256 `51a25b292da65e4dfce032bfb0d778c0364a31f2d779e8c989de54aebabb2675`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED UnsupportedTapeOperation: RBC E_TAPE_UNSUPPORTED: Line 8060: LOAD requires external tape I/O; RBC supports standalone BASIC programs only`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED UnsupportedTapeOperation: RBC E_TAPE_UNSUPPORTED: Line 8060: LOAD requires external tape I/O; RBC supports standalone BASIC programs only`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

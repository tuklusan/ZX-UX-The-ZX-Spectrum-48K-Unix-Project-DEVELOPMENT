The game requires tape LOAD, which this native compiler cannot safely support.

Original BASIC: `44-evolution-1.bas`; SHA-256: `51a25b292da65e4dfce032bfb0d778c0364a31f2d779e8c989de54aebabb2675`.

Original tape: `44-evolution-1.tzx`; SHA-256: `8e72b017a3cd647829f84fbecdb4b8e26a3bc08b20da66ffb8ebaecd91ed14fb`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED UnsupportedTapeOperation: RBC E_TAPE_UNSUPPORTED: Line 8060: LOAD requires external tape I/O; RBC supports standalone BASIC programs only`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED UnsupportedTapeOperation: RBC E_TAPE_UNSUPPORTED: Line 8060: LOAD requires external tape I/O; RBC supports standalone BASIC programs only`

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

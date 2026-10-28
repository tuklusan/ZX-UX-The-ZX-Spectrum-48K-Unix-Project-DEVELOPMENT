Dynamic DIM storage lacks a verified three-base native source build.

Original BASIC: `51-anagrammatic.bas`; SHA-256: `cabbe682fbeb79b7b1174dd8c73566cd31eec9b4251663d8c1d4255f1568dc3f`.

Original tape: `51-anagrammatic.tzx`; SHA-256: `55c33e31b3e0256fca660b7cec280a6ac5c1fde6070d5737038a8a46d4690b81`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

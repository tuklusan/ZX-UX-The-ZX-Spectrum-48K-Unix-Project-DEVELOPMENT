# 51-anagrammatic — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `cabbe682fbeb79b7b1174dd8c73566cd31eec9b4251663d8c1d4255f1568dc3f`
- TZX SHA-256: `55c33e31b3e0256fca660b7cec280a6ac5c1fde6070d5737038a8a46d4690b81`
- Independent TZX conversion: passed, 60 BASIC lines; decoded SHA-256 `cabbe682fbeb79b7b1174dd8c73566cd31eec9b4251663d8c1d4255f1568dc3f`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

# 36-postman — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `5754398693c6087dfdab78c65f6431caf66045e17e829482ff28988f499ed2cb`
- TZX SHA-256: `af112fd1bbff766a07a8a2c4b3856e9dcc59af96bdd67f3f22db9a8bd68e1213`
- Independent TZX conversion: passed, 91 BASIC lines; decoded SHA-256 `5754398693c6087dfdab78c65f6431caf66045e17e829482ff28988f499ed2cb`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

# 09-battleships — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `fb7cf8d9a0efb2d08c3bb9f61b3edfa7efafa5c9e5a90c0c7da5b7d03b0a9dc5`
- TZX SHA-256: `7a762cdcb14d04a8d8d8318c2eb7e8a273aab9ef46dbfa22194c3b2fac5ed8d4`
- Independent TZX conversion: passed, 131 BASIC lines; decoded SHA-256 `fb7cf8d9a0efb2d08c3bb9f61b3edfa7efafa5c9e5a90c0c7da5b7d03b0a9dc5`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: ZX-UX INPUT memory limit exceeded: file=14106, image=12519, bss=1459, stack=384, total=14362, max=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: ZX-UX INPUT memory limit exceeded: file=14106, image=12519, bss=1459, stack=384, total=14362, max=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

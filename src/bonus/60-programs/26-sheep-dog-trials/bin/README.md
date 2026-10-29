# 26-sheep-dog-trials — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `699f1f9f6d7d9ab7e84d971c0609589d48026f22526aa0fa7265bd68c81fdb06`
- TZX SHA-256: `8718bb6b4f886c8a4ce9459684cac6f0b66504d8a861bdb9559ad76938ab5e77`
- Independent TZX conversion: passed, 87 BASIC lines; decoded SHA-256 `699f1f9f6d7d9ab7e84d971c0609589d48026f22526aa0fa7265bd68c81fdb06`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

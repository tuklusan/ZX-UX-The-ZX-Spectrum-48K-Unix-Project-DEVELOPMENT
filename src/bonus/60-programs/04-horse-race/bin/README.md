# 04-horse-race — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `287bca8d30716200445d55dfc398a1b1bc9c166708c4ad721b884d7d877754f1`
- TZX SHA-256: `17e0fb5f040ca152f31954ccd1d34060af5ceca4fd21d0084aba0889d1276b72`
- Independent TZX conversion: passed, 99 BASIC lines; decoded SHA-256 `287bca8d30716200445d55dfc398a1b1bc9c166708c4ad721b884d7d877754f1`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

Dynamic DIM storage lacks a verified three-base native source build.

Original BASIC: `04-horse-race.bas`; SHA-256: `287bca8d30716200445d55dfc398a1b1bc9c166708c4ad721b884d7d877754f1`.

Original tape: `04-horse-race.tzx`; SHA-256: `17e0fb5f040ca152f31954ccd1d34060af5ceca4fd21d0084aba0889d1276b72`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

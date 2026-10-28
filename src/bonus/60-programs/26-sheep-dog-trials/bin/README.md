Dynamic DIM storage lacks a verified three-base native source build.

Original BASIC: `26-sheep-dog-trials.bas`; SHA-256: `699f1f9f6d7d9ab7e84d971c0609589d48026f22526aa0fa7265bd68c81fdb06`.

Original tape: `26-sheep-dog-trials.tzx`; SHA-256: `8718bb6b4f886c8a4ce9459684cac6f0b66504d8a861bdb9559ad76938ab5e77`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

Native Z80 source coverage is incomplete; compilation is blocked.

Original BASIC: `38-morse-tutor.bas`; SHA-256: `8f031a3a4bbe29bf91dd3ff0b3c9d70e4d5929aa74c5d30f3e1870de395ca45f`.

Original tape: `38-morse-tutor.tzx`; SHA-256: `cce431a4b92016d3da276c538f11fe6712ac1f4d10f8055119c74c841fe7a142`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: unresolved compiler bytes extend beyond native runtime`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: unresolved compiler bytes extend beyond native runtime`

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

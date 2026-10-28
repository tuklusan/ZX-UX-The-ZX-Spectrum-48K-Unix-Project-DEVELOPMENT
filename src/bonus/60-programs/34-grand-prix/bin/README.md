Native Z80 source coverage is incomplete; compilation is blocked.

Original BASIC: `34-grand-prix.bas`; SHA-256: `15b18cbfc506069bc38feba4f1aa5e18ffc8db948db04930695c6f48a5ad7836`.

Original tape: `34-grand-prix.tzx`; SHA-256: `c1d943b33b2431ed24e5e38b36d70b541428c11c6ed4baafcb36a979d5d43614`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: unresolved compiler bytes extend beyond native runtime`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: unresolved compiler bytes extend beyond native runtime`

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

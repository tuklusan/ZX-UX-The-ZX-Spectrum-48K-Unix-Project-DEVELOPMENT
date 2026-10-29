# 34-grand-prix — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `15b18cbfc506069bc38feba4f1aa5e18ffc8db948db04930695c6f48a5ad7836`
- TZX SHA-256: `c1d943b33b2431ed24e5e38b36d70b541428c11c6ed4baafcb36a979d5d43614`
- Independent TZX conversion: passed, 80 BASIC lines; decoded SHA-256 `15b18cbfc506069bc38feba4f1aa5e18ffc8db948db04930695c6f48a5ad7836`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: unresolved compiler bytes extend beyond native runtime`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: unresolved compiler bytes extend beyond native runtime`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

# 46-evolution-3 — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `8a8365c077e26e45ad3177fe261ea5499c4ded09914bc8bbb7b522900ae4aa74`
- TZX SHA-256: `46b313ae0de2ef231d051d0b47bcbb8f23a1d3e84c1c492d7d61f1b9b202ccd7`
- Independent TZX conversion: passed, 112 BASIC lines; decoded SHA-256 `8a8365c077e26e45ad3177fe261ea5499c4ded09914bc8bbb7b522900ae4aa74`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=14735, image=13051, bss=2006, stack=384, total=15441, limit=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=14735, image=13051, bss=2006, stack=384, total=15441, limit=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

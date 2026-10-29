# 27-picture-pairs — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `4c5f9c2a211883f4f6cd05af4abb7f6b7d974c51f44a5ef81ce4fb135628d895`
- TZX SHA-256: `0b20705fc318840e29056eb63df95a03a2b1ebc9b26f434398c3d2208f2ae494`
- Independent TZX conversion: passed, 111 BASIC lines; decoded SHA-256 `4c5f9c2a211883f4f6cd05af4abb7f6b7d974c51f44a5ef81ce4fb135628d895`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=15508, image=13861, bss=6426, stack=384, total=20671, limit=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=15508, image=13861, bss=6426, stack=384, total=20671, limit=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

# 44-evolution-1 — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `51a25b292da65e4dfce032bfb0d778c0364a31f2d779e8c989de54aebabb2675`
- TZX SHA-256: `8e72b017a3cd647829f84fbecdb4b8e26a3bc08b20da66ffb8ebaecd91ed14fb`
- Independent TZX conversion: passed, 108 BASIC lines; decoded SHA-256 `51a25b292da65e4dfce032bfb0d778c0364a31f2d779e8c989de54aebabb2675`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=14232, image=12571, bss=448, stack=384, total=13403, limit=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=14232, image=12571, bss=448, stack=384, total=13403, limit=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

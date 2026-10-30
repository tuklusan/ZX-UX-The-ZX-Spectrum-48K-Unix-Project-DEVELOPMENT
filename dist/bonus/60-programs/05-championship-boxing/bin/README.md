# 05-championship-boxing — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `f87e32c85f36b9ebadd7a9ac2f28eefde87400256ca0dfea3a85f138955fef1f`
- TZX SHA-256: `723cf70067eedcdd26aa0c17f0e54cf73b017b47b35582078c360e4965f77cb8`
- Independent TZX conversion: passed, 130 BASIC lines; decoded SHA-256 `f87e32c85f36b9ebadd7a9ac2f28eefde87400256ca0dfea3a85f138955fef1f`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=15934, image=13918, bss=940, stack=384, total=15242, limit=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=15934, image=13918, bss=940, stack=384, total=15242, limit=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

# 20-ambush — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `0120e802884977481127ce5f2ec21aa323ff14c170356b44b7caa1cf6945367e`
- TZX SHA-256: `d5f05e24af01297db1c85909b433c7fe18f3465f4e79767f3c13b77a07aa7809`
- Independent TZX conversion: passed, 122 BASIC lines; decoded SHA-256 `0120e802884977481127ce5f2ec21aa323ff14c170356b44b7caa1cf6945367e`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=14241, image=12489, bss=2227, stack=384, total=15100, limit=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=14241, image=12489, bss=2227, stack=384, total=15100, limit=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

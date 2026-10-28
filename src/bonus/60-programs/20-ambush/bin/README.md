Native program is too large for the 14,000-byte loader limit.

Original BASIC: `20-ambush.bas`; SHA-256: `0120e802884977481127ce5f2ec21aa323ff14c170356b44b7caa1cf6945367e`.

Original tape: `20-ambush.tzx`; SHA-256: `d5f05e24af01297db1c85909b433c7fe18f3465f4e79767f3c13b77a07aa7809`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=13911, image=12159, bss=2227, stack=384, total=14770, limit=14000`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=13911, image=12159, bss=2227, stack=384, total=14770, limit=14000`

Measured link values from the failing baseline: file 13911, image 12159, BSS 2227, stack 384, total 14770 bytes; permitted maximum 14000 bytes. These are diagnostics, not a published executable.

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

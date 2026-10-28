Native program is too large for the 14,000-byte loader limit.

Original BASIC: `19-hobday-expenses.bas`; SHA-256: `5bd580896384975ecbcecda2a7975b4c08f69b53ee38b2563c40e9992598983b`.

Original tape: `19-hobday-expenses.tzx`; SHA-256: `935da8554d1fa0ee633d8055ab39917e933d1026aed63cb86e6c7610fb437b86`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=19735, image=17320, bss=2586, stack=384, total=20290, limit=14000`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=19735, image=17320, bss=2586, stack=384, total=20290, limit=14000`

Measured link values from the failing baseline: file 19735, image 17320, BSS 2586, stack 384, total 20290 bytes; permitted maximum 14000 bytes. These are diagnostics, not a published executable.

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

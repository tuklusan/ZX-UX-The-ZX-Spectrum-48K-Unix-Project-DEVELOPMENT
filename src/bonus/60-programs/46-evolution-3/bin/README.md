Native program is too large for the 14,000-byte loader limit.

Original BASIC: `46-evolution-3.bas`; SHA-256: `8a8365c077e26e45ad3177fe261ea5499c4ded09914bc8bbb7b522900ae4aa74`.

Original tape: `46-evolution-3.tzx`; SHA-256: `46b313ae0de2ef231d051d0b47bcbb8f23a1d3e84c1c492d7d61f1b9b202ccd7`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=14075, image=12391, bss=1237, stack=384, total=14012, limit=14000`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=14075, image=12391, bss=1237, stack=384, total=14012, limit=14000`

Measured link values from the failing baseline: file 14075, image 12391, BSS 1237, stack 384, total 14012 bytes; permitted maximum 14000 bytes. These are diagnostics, not a published executable.

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

Native program is too large for the 14,000-byte loader limit.

Original BASIC: `27-picture-pairs.bas`; SHA-256: `4c5f9c2a211883f4f6cd05af4abb7f6b7d974c51f44a5ef81ce4fb135628d895`.

Original tape: `27-picture-pairs.tzx`; SHA-256: `0b20705fc318840e29056eb63df95a03a2b1ebc9b26f434398c3d2208f2ae494`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=15268, image=13621, bss=6426, stack=384, total=20431, limit=14000`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=15268, image=13621, bss=6426, stack=384, total=20431, limit=14000`

Measured link values from the failing baseline: file 15268, image 13621, BSS 6426, stack 384, total 20431 bytes; permitted maximum 14000 bytes. These are diagnostics, not a published executable.

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

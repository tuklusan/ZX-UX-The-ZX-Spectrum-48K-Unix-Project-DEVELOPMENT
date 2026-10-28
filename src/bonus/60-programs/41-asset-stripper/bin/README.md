Native program is too large for the 14,000-byte loader limit.

Original BASIC: `41-asset-stripper.bas`; SHA-256: `5e9cccfbf1f3b3f893c503212d772d4d021c957a04ab6bb988a5f43448b5f053`.

Original tape: `41-asset-stripper.tzx`; SHA-256: `b95574502c440886418a4e8f220f2f8daba5c4d0b1bb3a12081860f3fdba5e53`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=19890, image=16944, bss=3243, stack=384, total=20571, limit=14000`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=19890, image=16944, bss=3243, stack=384, total=20571, limit=14000`

Measured link values from the failing baseline: file 19890, image 16944, BSS 3243, stack 384, total 20571 bytes; permitted maximum 14000 bytes. These are diagnostics, not a published executable.

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

Native program is too large for the 14,000-byte loader limit.

Original BASIC: `02-fall-guy.bas`; SHA-256: `51e440470d18c999ea3322dd0fedb6e3486dd15bf62c838ae5038e341a8db2d4`.

Original tape: `02-fall-guy.tzx`; SHA-256: `9d1bee9267ed842174fb7772a5ad7859ffab0140bcf1854da5af2e432ff2a843`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=14147, image=12395, bss=1247, stack=384, total=14026, max=14000`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=14147, image=12395, bss=1247, stack=384, total=14026, max=14000`

Measured link values from the failing baseline: file 14147, image 12395, BSS 1247, stack 384, total 14026 bytes; permitted maximum 14000 bytes. These are diagnostics, not a published executable.

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

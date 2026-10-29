# 02-fall-guy — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `51e440470d18c999ea3322dd0fedb6e3486dd15bf62c838ae5038e341a8db2d4`
- TZX SHA-256: `9d1bee9267ed842174fb7772a5ad7859ffab0140bcf1854da5af2e432ff2a843`
- Independent TZX conversion: passed, 100 BASIC lines; decoded SHA-256 `51e440470d18c999ea3322dd0fedb6e3486dd15bf62c838ae5038e341a8db2d4`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: ZX-UX INPUT memory limit exceeded: file=15018, image=13197, bss=4064, stack=384, total=17645, max=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: ZX-UX INPUT memory limit exceeded: file=15018, image=13197, bss=4064, stack=384, total=17645, max=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

Native program is too large for the 14,000-byte loader limit.

Original BASIC: `08-chomper.bas`; SHA-256: `8a66d4ea87462481193e639d350fdf87d82fa832f902e71ee2b5ebfe32fa51cb`.

Original tape: `08-chomper.tzx`; SHA-256: `d986a1d7bc5b45cbd29e9a3c0587008076facba430ca55ecae651aed06782a48`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=14211, image=12933, bss=132, stack=384, total=13449, max=14000`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=14211, image=12933, bss=132, stack=384, total=13449, max=14000`

Measured link values from the failing baseline: file 14211, image 12933, BSS 132, stack 384, total 13449 bytes; permitted maximum 14000 bytes. These are diagnostics, not a published executable.

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

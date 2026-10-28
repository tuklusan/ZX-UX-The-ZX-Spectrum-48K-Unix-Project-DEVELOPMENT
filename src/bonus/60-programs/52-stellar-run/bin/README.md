Native program is too large for the 14,000-byte loader limit.

Original BASIC: `52-stellar-run.bas`; SHA-256: `854f21f382fa1b818aa6895ad700b0279570d8e2eb42453d8e6c93e300f100f3`.

Original tape: `52-stellar-run.tzx`; SHA-256: `765ae45397f894327e7fbb543ae2cdfd3d13946510076534cc4fc209a88610f2`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=13108, image=11537, bss=3273, stack=384, total=15194, max=14000`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=13108, image=11537, bss=3273, stack=384, total=15194, max=14000`

Measured link values from the failing baseline: file 13108, image 11537, BSS 3273, stack 384, total 15194 bytes; permitted maximum 14000 bytes. These are diagnostics, not a published executable.

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

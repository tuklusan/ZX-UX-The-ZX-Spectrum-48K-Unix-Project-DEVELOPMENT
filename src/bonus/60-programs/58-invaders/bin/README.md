Native program is too large for the 14,000-byte loader limit.

Original BASIC: `58-invaders.bas`; SHA-256: `ced3897dce16a21d555ad4bc6e26b63a36ae4028fe36ce44dabd4cb85349d6f5`.

Original tape: `58-invaders.tzx`; SHA-256: `2332416e06e6387faabe7cc587731e1eb003255e0bf933d12fdad8902f5157d7`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=13319, image=11783, bss=1956, stack=384, total=14123, max=14000`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=13319, image=11783, bss=1956, stack=384, total=14123, max=14000`

Measured link values from the failing baseline: file 13319, image 11783, BSS 1956, stack 384, total 14123 bytes; permitted maximum 14000 bytes. These are diagnostics, not a published executable.

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

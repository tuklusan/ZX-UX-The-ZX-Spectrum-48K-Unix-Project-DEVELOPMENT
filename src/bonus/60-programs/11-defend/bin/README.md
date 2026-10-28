Native program is too large for the 14,000-byte loader limit.

Original BASIC: `11-defend.bas`; SHA-256: `261d8ea20f7c57fe047275de3b0b9a1791eb803bba91d225304255eb0f3ff4a2`.

Original tape: `11-defend.tzx`; SHA-256: `1101e4d31798bca76d6ec7157f8820995356a6f3803d1cb09002461561d8a800`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=14725, image=13036, bss=955, stack=384, total=14375, max=14000`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=14725, image=13036, bss=955, stack=384, total=14375, max=14000`

Measured link values from the failing baseline: file 14725, image 13036, BSS 955, stack 384, total 14375 bytes; permitted maximum 14000 bytes. These are diagnostics, not a published executable.

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

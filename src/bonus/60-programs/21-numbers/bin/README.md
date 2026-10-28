Native program is too large for the 14,000-byte loader limit.

Original BASIC: `21-numbers.bas`; SHA-256: `ab2625f8b40e7b0cf98258d9c544a5d9142928906ad60bbfc67105c4666243ed`.

Original tape: `21-numbers.tzx`; SHA-256: `8e0afa7b5c7c5d1f34f8e259f03085ca414d337661eee23fbf682d423bdfeb91`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=15146, image=13669, bss=803, stack=384, total=14856, max=14000`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=15146, image=13669, bss=803, stack=384, total=14856, max=14000`

Measured link values from the failing baseline: file 15146, image 13669, BSS 803, stack 384, total 14856 bytes; permitted maximum 14000 bytes. These are diagnostics, not a published executable.

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

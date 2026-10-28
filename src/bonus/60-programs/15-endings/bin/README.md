Native program is too large for the 14,000-byte loader limit.

Original BASIC: `15-endings.bas`; SHA-256: `0943182da0f3b9100603de66ea56a648e02648a37f6a0eea55e1eb845dbcdea2`.

Original tape: `15-endings.tzx`; SHA-256: `c695f76fd2e2f4a1f80c8f52e8fc1f9d8eedaed92668e420a07cdfa5c88f545f`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=10710, image=9636, bss=4081, stack=384, total=14101, max=14000`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=10710, image=9636, bss=4081, stack=384, total=14101, max=14000`

Measured link values from the failing baseline: file 10710, image 9636, BSS 4081, stack 384, total 14101 bytes; permitted maximum 14000 bytes. These are diagnostics, not a published executable.

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

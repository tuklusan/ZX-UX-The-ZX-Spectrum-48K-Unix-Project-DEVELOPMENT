Native program is too large for the 14,000-byte loader limit.

Original BASIC: `48-energy-field.bas`; SHA-256: `63c42b83a4a70662506caf9c4775b09c43e3e7e0265a8978928bb4e81135af5a`.

Original tape: `48-energy-field.tzx`; SHA-256: `5949ea3895dd562494cdb9458298ab3e0f50fad0a559b8b8e5e7aa5c925d4969`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=15136, image=13352, bss=643, stack=384, total=14379, max=14000`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=15136, image=13352, bss=643, stack=384, total=14379, max=14000`

Measured link values from the failing baseline: file 15136, image 13352, BSS 643, stack 384, total 14379 bytes; permitted maximum 14000 bytes. These are diagnostics, not a published executable.

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

The emitted pre-link source layout cannot be safely assembled.

Original BASIC: `53-russian-roulette.bas`; SHA-256: `2f7069cb8a179fc6a14a8e099746a836595ec6703f4786f6830a880bd6b4a0c1`.

Original tape: `53-russian-roulette.tzx`; SHA-256: `e3c2ca43759f727222cac68a6bed3358026a58344cce220a3db7c12516ab7ced`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED NativeWrapperError: unsupported original pre-link source layout`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED NativeWrapperError: unsupported original pre-link source layout`

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

Native Z80 source coverage is incomplete; compilation is blocked.

Original BASIC: `05-championship-boxing.bas`; SHA-256: `f87e32c85f36b9ebadd7a9ac2f28eefde87400256ca0dfea3a85f138955fef1f`.

Original tape: `05-championship-boxing.tzx`; SHA-256: `723cf70067eedcdd26aa0c17f0e54cf73b017b47b35582078c360e4965f77cb8`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: unresolved compiler bytes extend beyond native runtime`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: unresolved compiler bytes extend beyond native runtime`

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

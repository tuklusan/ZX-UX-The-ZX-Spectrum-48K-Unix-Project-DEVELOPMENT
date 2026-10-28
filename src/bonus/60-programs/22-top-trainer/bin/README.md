The HiSoft compiler did not provide the complete required native image.

Original BASIC: `22-top-trainer.bas`; SHA-256: `af21d2028be31b57f6fb27d613be72588d9dc0aa7da56fa7010e81d29a18d353`.

Original tape: `22-top-trainer.tzx`; SHA-256: `9b2d55288d71aa03d1f2f111e5ccd17a6ce45379b0a930a886adb7c5af59ef18`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: the full compiled mode C image is required`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: the full compiled mode C image is required`

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

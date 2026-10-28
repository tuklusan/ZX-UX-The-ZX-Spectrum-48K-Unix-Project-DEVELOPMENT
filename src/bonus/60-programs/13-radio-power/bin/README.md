The HiSoft compiler did not provide the complete required native image.

Original BASIC: `13-radio-power.bas`; SHA-256: `b1c0bb3fbcb3d2d3f57ec5ad6dc60a5dc29253ee47bb371dbc42bb3de96dadaa`.

Original tape: `13-radio-power.tzx`; SHA-256: `4550f11d0b8a7973ed4f05f80e7d147c1745a56a7dc2deeb30334d17983e9034`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: the full compiled mode C image is required`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: the full compiled mode C image is required`

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

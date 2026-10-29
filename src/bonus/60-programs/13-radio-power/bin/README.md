# 13-radio-power — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `b1c0bb3fbcb3d2d3f57ec5ad6dc60a5dc29253ee47bb371dbc42bb3de96dadaa`
- TZX SHA-256: `4550f11d0b8a7973ed4f05f80e7d147c1745a56a7dc2deeb30334d17983e9034`
- Independent TZX conversion: passed, 256 BASIC lines; decoded SHA-256 `b1c0bb3fbcb3d2d3f57ec5ad6dc60a5dc29253ee47bb371dbc42bb3de96dadaa`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: the full compiled mode C image is required`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: the full compiled mode C image is required`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

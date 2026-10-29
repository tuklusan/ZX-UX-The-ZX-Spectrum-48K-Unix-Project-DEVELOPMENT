# 55-hangman — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `cb5ea3c45034d8f7e9fa90204b81156e44f1c034aeadfe7e9a24016ffba36f6c`
- TZX SHA-256: `befba19de249029fb400d227888baf4074f77803019248ea3fa4d8b68f9f49be`
- Independent TZX conversion: passed, 79 BASIC lines; decoded SHA-256 `cb5ea3c45034d8f7e9fa90204b81156e44f1c034aeadfe7e9a24016ffba36f6c`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED UnsupportedUsr: RBC E_MACHINE_CODE: Line 7080: Numeric USR is prohibited`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED UnsupportedUsr: RBC E_MACHINE_CODE: Line 7080: Numeric USR is prohibited`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

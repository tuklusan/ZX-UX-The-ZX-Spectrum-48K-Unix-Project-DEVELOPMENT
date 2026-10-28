The game makes a prohibited numeric USR machine-code call.

Original BASIC: `55-hangman.bas`; SHA-256: `cb5ea3c45034d8f7e9fa90204b81156e44f1c034aeadfe7e9a24016ffba36f6c`.

Original tape: `55-hangman.tzx`; SHA-256: `befba19de249029fb400d227888baf4074f77803019248ea3fa4d8b68f9f49be`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED UnsupportedUsr: RBC E_MACHINE_CODE: Line 7080: Numeric USR is prohibited`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED UnsupportedUsr: RBC E_MACHINE_CODE: Line 7080: Numeric USR is prohibited`

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

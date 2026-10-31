# 55-hangman — Native RBC result

Original BASIC and tokenized tape were kept unchanged.
- Independent TZX conversion: passed, 79 BASIC lines.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED UnsupportedUsr: RBC E_MACHINE_CODE: Line 7080: Numeric USR is prohibited`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED UnsupportedUsr: RBC E_MACHINE_CODE: Line 7080: Numeric USR is prohibited`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

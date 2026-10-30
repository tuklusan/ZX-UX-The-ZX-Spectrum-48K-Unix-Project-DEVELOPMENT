# 38-morse-tutor — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `8f031a3a4bbe29bf91dd3ff0b3c9d70e4d5929aa74c5d30f3e1870de395ca45f`
- TZX SHA-256: `cce431a4b92016d3da276c538f11fe6712ac1f4d10f8055119c74c841fe7a142`
- Independent TZX conversion: passed, 132 BASIC lines; decoded SHA-256 `8f031a3a4bbe29bf91dd3ff0b3c9d70e4d5929aa74c5d30f3e1870de395ca45f`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: ZX-UX INPUT memory limit exceeded: file=11940, image=10705, bss=5191, stack=384, total=16280, max=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: ZX-UX INPUT memory limit exceeded: file=11940, image=10705, bss=5191, stack=384, total=16280, max=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

# 16-snap — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `bafb27e17cbeb2d437dfa0b00227a5af42a06b2dd80ba335779a5bb4d0545e5e`
- TZX SHA-256: `1c870d0ead54257211bdbd4930da9f58332d18559977ac53bd90bfd9b44ae0d1`
- Independent TZX conversion: passed, 62 BASIC lines; decoded SHA-256 `bafb27e17cbeb2d437dfa0b00227a5af42a06b2dd80ba335779a5bb4d0545e5e`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: ZX-UX INPUT memory limit exceeded: file=11006, image=10115, bss=4197, stack=384, total=14696, max=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: ZX-UX INPUT memory limit exceeded: file=11006, image=10115, bss=4197, stack=384, total=14696, max=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

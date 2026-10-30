# 11-defend — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `261d8ea20f7c57fe047275de3b0b9a1791eb803bba91d225304255eb0f3ff4a2`
- TZX SHA-256: `1101e4d31798bca76d6ec7157f8820995356a6f3803d1cb09002461561d8a800`
- Independent TZX conversion: passed, 125 BASIC lines; decoded SHA-256 `261d8ea20f7c57fe047275de3b0b9a1791eb803bba91d225304255eb0f3ff4a2`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=15305, image=13597, bss=1979, stack=384, total=15960, max=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=15305, image=13597, bss=1979, stack=384, total=15960, max=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

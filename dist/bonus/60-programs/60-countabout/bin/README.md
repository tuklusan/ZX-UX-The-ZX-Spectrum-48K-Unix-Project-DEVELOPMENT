# 60-countabout — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `2147bc9a6aed314075e9257eca9c671d7de922b051fb36e6e8faf82dc7703294`
- TZX SHA-256: `2e947f6969b718df6f308d1254ce9320811e4129712433f6314f62d068453b8b`
- Independent TZX conversion: passed, 143 BASIC lines; decoded SHA-256 `2147bc9a6aed314075e9257eca9c671d7de922b051fb36e6e8faf82dc7703294`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=13800, image=12341, bss=2024, stack=384, total=14749, max=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=13800, image=12341, bss=2024, stack=384, total=14749, max=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

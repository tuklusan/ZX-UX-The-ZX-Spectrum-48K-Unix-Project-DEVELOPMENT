# 48-energy-field — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `63c42b83a4a70662506caf9c4775b09c43e3e7e0265a8978928bb4e81135af5a`
- TZX SHA-256: `5949ea3895dd562494cdb9458298ab3e0f50fad0a559b8b8e5e7aa5c925d4969`
- Independent TZX conversion: passed, 158 BASIC lines; decoded SHA-256 `63c42b83a4a70662506caf9c4775b09c43e3e7e0265a8978928bb4e81135af5a`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=15506, image=13703, bss=1667, stack=384, total=15754, max=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=15506, image=13703, bss=1667, stack=384, total=15754, max=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

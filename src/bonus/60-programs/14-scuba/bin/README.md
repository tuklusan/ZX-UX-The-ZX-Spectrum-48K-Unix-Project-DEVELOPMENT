# 14-scuba — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `55f843260e3ead814cdae91e3e84590d35eea2740d6ed9cb49b9d628c626af74`
- TZX SHA-256: `26b31f55aa6219740e3d64fa7a3f1c49f36d035d30cd4f663daf8bdba31e3f92`
- Independent TZX conversion: passed, 202 BASIC lines; decoded SHA-256 `55f843260e3ead814cdae91e3e84590d35eea2740d6ed9cb49b9d628c626af74`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=14365, image=12691, bss=1886, stack=384, total=14961, max=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=14365, image=12691, bss=1886, stack=384, total=14961, max=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

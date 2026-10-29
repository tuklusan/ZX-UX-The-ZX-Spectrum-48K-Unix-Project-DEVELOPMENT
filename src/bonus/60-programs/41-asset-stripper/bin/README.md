# 41-asset-stripper — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `5e9cccfbf1f3b3f893c503212d772d4d021c957a04ab6bb988a5f43448b5f053`
- TZX SHA-256: `b95574502c440886418a4e8f220f2f8daba5c4d0b1bb3a12081860f3fdba5e53`
- Independent TZX conversion: passed, 339 BASIC lines; decoded SHA-256 `5e9cccfbf1f3b3f893c503212d772d4d021c957a04ab6bb988a5f43448b5f053`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=20550, image=17604, bss=3243, stack=384, total=21231, limit=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=20550, image=17604, bss=3243, stack=384, total=21231, limit=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

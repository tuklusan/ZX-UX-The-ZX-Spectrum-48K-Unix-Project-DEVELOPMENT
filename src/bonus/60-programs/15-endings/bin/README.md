# 15-endings — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `0943182da0f3b9100603de66ea56a648e02648a37f6a0eea55e1eb845dbcdea2`
- TZX SHA-256: `c695f76fd2e2f4a1f80c8f52e8fc1f9d8eedaed92668e420a07cdfa5c88f545f`
- Independent TZX conversion: passed, 185 BASIC lines; decoded SHA-256 `0943182da0f3b9100603de66ea56a648e02648a37f6a0eea55e1eb845dbcdea2`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=10078, image=9024, bss=4850, stack=384, total=14258, limit=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=10078, image=9024, bss=4850, stack=384, total=14258, limit=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

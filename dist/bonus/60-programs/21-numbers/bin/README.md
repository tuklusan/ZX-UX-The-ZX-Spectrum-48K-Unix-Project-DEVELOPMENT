# 21-numbers — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `ab2625f8b40e7b0cf98258d9c544a5d9142928906ad60bbfc67105c4666243ed`
- TZX SHA-256: `8e0afa7b5c7c5d1f34f8e259f03085ca414d337661eee23fbf682d423bdfeb91`
- Independent TZX conversion: passed, 121 BASIC lines; decoded SHA-256 `ab2625f8b40e7b0cf98258d9c544a5d9142928906ad60bbfc67105c4666243ed`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=14094, image=12637, bss=803, stack=384, total=13824, limit=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=14094, image=12637, bss=803, stack=384, total=13824, limit=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

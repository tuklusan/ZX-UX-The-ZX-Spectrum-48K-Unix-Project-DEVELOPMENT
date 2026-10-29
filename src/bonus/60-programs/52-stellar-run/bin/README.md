# 52-stellar-run — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `854f21f382fa1b818aa6895ad700b0279570d8e2eb42453d8e6c93e300f100f3`
- TZX SHA-256: `765ae45397f894327e7fbb543ae2cdfd3d13946510076534cc4fc209a88610f2`
- Independent TZX conversion: passed, 138 BASIC lines; decoded SHA-256 `854f21f382fa1b818aa6895ad700b0279570d8e2eb42453d8e6c93e300f100f3`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=12596, image=11045, bss=4811, stack=384, total=16240, limit=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: original typed three-base HiSoft source unresolved: native source baseline exceeds default memory limit: file=12596, image=11045, bss=4811, stack=384, total=16240, limit=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

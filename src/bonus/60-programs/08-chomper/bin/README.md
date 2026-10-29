# 08-chomper — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `8a66d4ea87462481193e639d350fdf87d82fa832f902e71ee2b5ebfe32fa51cb`
- TZX SHA-256: `d986a1d7bc5b45cbd29e9a3c0587008076facba430ca55ecae651aed06782a48`
- Independent TZX conversion: passed, 103 BASIC lines; decoded SHA-256 `8a66d4ea87462481193e639d350fdf87d82fa832f902e71ee2b5ebfe32fa51cb`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=14671, image=13374, bss=1156, stack=384, total=14914, max=14000`

- TZX: exit 1

  Diagnostic: `RBC_NATIVE_BLOCKED ValueError: native memory limit exceeded: file=14671, image=13374, bss=1156, stack=384, total=14914, max=14000`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

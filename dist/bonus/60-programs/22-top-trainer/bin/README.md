# 22-top-trainer — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `af21d2028be31b57f6fb27d613be72588d9dc0aa7da56fa7010e81d29a18d353`
- TZX SHA-256: `9b2d55288d71aa03d1f2f111e5ccd17a6ce45379b0a930a886adb7c5af59ef18`
- Independent TZX conversion: passed, 323 BASIC lines; decoded SHA-256 `af21d2028be31b57f6fb27d613be72588d9dc0aa7da56fa7010e81d29a18d353`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `%RBC-WARNING RBC_WARN_HISOFT_SPLIT_IMAGE Line: - Statement: - HiSoft returned a combined D+E image rather than a single C-mode capture. The complete native source must be reconstructed before linking. | RBC_NATIVE_BLOCKED ValueError: the full compiled mode C image is required`

- TZX: exit 1

  Diagnostic: `%RBC-WARNING RBC_WARN_HISOFT_SPLIT_IMAGE Line: - Statement: - HiSoft returned a combined D+E image rather than a single C-mode capture. The complete native source must be reconstructed before linking. | RBC_NATIVE_BLOCKED ValueError: the full compiled mode C image is required`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

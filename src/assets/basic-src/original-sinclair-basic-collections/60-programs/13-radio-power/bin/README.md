# 13-radio-power — Native RBC result

Original BASIC and tokenized tape were kept unchanged.
- Independent TZX conversion: passed, 256 BASIC lines.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `%RBC-WARNING RBC_WARN_HISOFT_SPLIT_IMAGE Line: - Statement: - HiSoft returned a combined D+E image rather than a single C-mode capture. The complete native source must be reconstructed before linking. | RBC_NATIVE_BLOCKED ValueError: the full compiled mode C image is required`

- TZX: exit 1

  Diagnostic: `%RBC-WARNING RBC_WARN_HISOFT_SPLIT_IMAGE Line: - Statement: - HiSoft returned a combined D+E image rather than a single C-mode capture. The complete native source must be reconstructed before linking. | RBC_NATIVE_BLOCKED ValueError: the full compiled mode C image is required`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

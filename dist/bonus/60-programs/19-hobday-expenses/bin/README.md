# 19-hobday-expenses — Native RBC result

Original BASIC and tokenized tape were kept unchanged.

- BAS SHA-256: `5bd580896384975ecbcecda2a7975b4c08f69b53ee38b2563c40e9992598983b`
- TZX SHA-256: `935da8554d1fa0ee633d8055ab39917e933d1026aed63cb86e6c7610fb437b86`
- Independent TZX conversion: passed, 192 BASIC lines; decoded SHA-256 `5bd580896384975ecbcecda2a7975b4c08f69b53ee38b2563c40e9992598983b`.
- Compiler: checked HiSoft source, strict ROM syntax, real native ras/rld, no optimizer, maximum 14000 bytes, stack 384 bytes.

- BAS: exit 1

  Diagnostic: `%RBC-WARNING RBC_WARN_HISOFT_SPLIT_IMAGE Line: - Statement: - HiSoft returned a combined D+E image rather than a single C-mode capture. The complete native source must be reconstructed before linking. | RBC_NATIVE_BLOCKED ValueError: the full compiled mode C image is required`

- TZX: exit 1

  Diagnostic: `%RBC-WARNING RBC_WARN_HISOFT_SPLIT_IMAGE Line: - Statement: - HiSoft returned a combined D+E image rather than a single C-mode capture. The complete native source must be reconstructed before linking. | RBC_NATIVE_BLOCKED ValueError: the full compiled mode C image is required`

- Comparison: unavailable. At least one compiler path refused a native build.

No native SSX is published. A failed or oversized build is not executable gameplay proof.

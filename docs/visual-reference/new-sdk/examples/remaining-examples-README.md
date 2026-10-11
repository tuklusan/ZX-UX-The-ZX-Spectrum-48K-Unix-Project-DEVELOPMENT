# C48 SDK visual check: remaining examples

The checked new SDK ran existing bytecode for `maze` and `argv` in its host runtime. Each produced a screen image, comparison difference, and JSON record with source and output hashes. The reference images are the original old SDK captures under `docs/visual-reference/old-sdk/examples/`.

- `maze`: 0 differing RGB pixels after a verified exact threefold normalization of the historical 768-by-576 PNG. This is a matching host SDK output image, not an emulator/native execution proof.
- `argv`: 728 differing RGB pixels. This comparison is inconclusive because the historical argument list and capture frame are not established. Do not report it as a visual pass or a confirmed compiler defect.

Both checked output directories passed the private checker. The old kernel and current ZX-UX native state comparisons remain pending. The proof data is retained without substituting or retouching historical screenshots.

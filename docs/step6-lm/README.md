# ZX-UX C48 LM — checked new-SDK host run

Status: successful **host SDK behavior test**, not native ZX-UX v1 execution. The owner waived the requirement to repeat the old SDK/kernel LM test.

Program: `ailmzx48`, from the already checked new C48 SDK checkpoint. Existing bytecode was reused; no new compilation was needed for this test.

- C48 source: `usr/src/ailmzx48/ailmzx48.c`; SHA-256 `c401a3fe1877033faef537449255faba075a0578d9fb7da0a5f4dbb113a4eea2`.
- Bytecode: `usr/bin/ailmzx48/ailmzx48.c48b`; size 1,748,291 bytes; SHA-256 `ae20ceec1ed753f6fe6d5f60745633e943002a2ec0755a4abe40b5133bf6c4c8`.
- New runtime: `compiler/c48run.py`, checked SDK checkpoint `cf12c33b523930dbe93e925e5a2acc4f559ec23ef0709c9a3cb63eab7ad14ab1`.
- Input: ASCII `hello` followed by LF, then `q` followed by LF, supplied through standard input.
- Runtime limits: 25-second time quota and 5,000,000-step VM ceiling; actual host return code 0.
- Actual observed result: welcome text, `hello` prompt and response, then `q` and clean exit. Audio playback dependency was unavailable; audible output was not tested.
- Authentic captured screen: `ailmzx48-host-hello.scr`, exactly 6,912 bytes; SHA-256 `a43124ff2830bd8ecb69527b5cd4d1496a729440108850a6503dfefda0eb2302`.
- `ailmzx48-host-hello.png` is a 256 by 192 rendering of those screen bytes using the checked new SDK's Spectrum display renderer and font; SHA-256 `ccb0be14e557ed289acf9e3838335509c6f25c24443e653213dd03da539d8cc0`.
- Private checker self-test: 491 passed. The source run command, output paths, screen bytes, and rendered PNG passed the private checker. All restricted-text rules remained unchanged.

This 1,748,291-byte program is much larger than the ZX Spectrum's total 48K RAM and cannot be treated as a proven native loadable image. This result establishes host SDK behavior only. It does not certify native LM loading, filesystem model-data access, all runtime services, or the ZX-UX v1 release.

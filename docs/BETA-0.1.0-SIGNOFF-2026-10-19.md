# ZX-UX beta-0.1.0 release record — 2026-10-19

Repository: `tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT`

Starting `main`: `b9901a92e2f9c39a48194b69e342a7c96dce1fef`.
Earlier tag `beta-0.0.9` remains unchanged.

The minimal release entry point is `python3 tools/release.py`. It compiles the
kernel and C48 portfolio, runs the selected checks, and records the actual
Spectrum screen in RVM and independent Fuse SDL. Fuse gallery capture may use
six separate X displays at once; every image comes directly from its own
emulator session. No screenshots are drawn, retouched, or combined.

## Build and loader

- Kernel: 8,183 bytes, below the 8 KB limit.
- The rebuilt ZX-UX boot cassette has four ROM blocks and 24 checked turbo
  packets. Its linked low kernel, full kernel, file system, and bootstrap match
  the rebuilt program.
- BALL uses the separate objects `ball-c.sso` and `ball-asm.sso`, plus the
  unmodified generic `libc48.ssa`; final files are `ball.ssx` and `ball.tzx`.
- Invaders uses `invaders-c.sso`, `invaders-asm.sso`, and the same generic
  library; final files are `invaders.ssx` and `invaders.tzx`.
- Both native SSX1 programs passed format, symbol, and memory checks. Their
  matching TZX cassettes each contain a single program header and data block.
- A bare `/dev/cassette/` prints a missing-name error without requesting a tape
  block. The explicit `/dev/cassette/*` starts BALL from the first eligible tape
  program. The named loader prints its accepted name before body loading.
- Extraction prints the actual archive filename. A real kernel check with
  `/tmp/x` confirmed extraction output and unchanged, non-duplicated `tar tf`
  listing output.

## New game behavior

Native ZX-UX RVM checks passed for BALL animation, with the left half
of the shared screen unchanged. Invaders checks passed: M starts play, C moves right,
Z moves left, M fires, Y restarts, and N exits. The Y/N check makes the game
reach its real replay code quickly by setting the lives counter to zero in
test RAM; it does not change the distributed binary or any gallery image.

## Release galleries

The release command captures 63 PNGs for RVM and 63 for Fuse SDL, including the
two multitasking scenes in each engine. Capture timing is independent of
functional-test arguments. Julia and Mandelbrot run until their first fractal
is complete, Torus runs into its wireframe scene, and Kaleido is captured while
running. BALL is captured during animation and Invaders during gameplay.

## Local verification

The release command runs the C48 constant, kernel/tape, turbo packet, boot,
and new game/cassette checks before generating both full galleries. The private
checker checks text and skips image and binary contents entirely. The checker
itself is kept outside this repository.

Publication is complete only after all generated files are present in remote
GitHub `main` and match the tested local tree. The `beta-0.1.0` tag is cut from
the verified final commit, without changing the earlier release tag.

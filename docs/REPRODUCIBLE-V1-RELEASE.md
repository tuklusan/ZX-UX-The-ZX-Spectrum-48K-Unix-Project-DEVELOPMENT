# Reproducing ZX-UX v1 from a clean checkout

This procedure does not use GitHub Actions, the retired ZX-UX kernel, or
the retired C48 compiler. The active SDK and the 56 C48 program sources
are part of this repository. Historical comparisons are a separate audit,
not a source of executable or object formats for v1.

## Required external environment

- Linux x86-64 with Python 3, Pillow, Xvfb and FUSE SDL 1.6.0.
- Checked SJASMPlus 1.24.0, SkoolKit 10.1 with its C simulator and
  16,384-byte Spectrum 48K ROM, and SkoolKit's tape converter.
- The owner's private ZX-UX checker, kept outside this checkout.
- The checked FUSE runtime assets and shared libraries, outside Git.

Inspect and verify the external tools before running them. The release
script validates the exact approved hashes of the assembler, simulator
and 48K ROM. Additional external-tool validation is documented in the
private checker's README. Do not copy private rules or third-party tool
files into this repository or its release outputs.

## One mandatory release command

Use a clean checked-out commit. From its root, with the external tools
available and SkoolKit 10.1 on `PYTHONPATH`:

```sh
python3 tools/release_v1.py \
  --checker /private/zxux/checker.py \
  --sjasm /tools/bin/sjasmplus \
  --tap2sna /tools/bin/tap2sna.py \
  --fuse-test-command 'python3 -B tests/fuse_boot.py --fuse /tools/fuse/fuse-sdl --rom /tools/rom/48.rom --tape build/ZX-UX.tzx --assets /tools/fuse/assets --libdir /tools/fuse/lib --screen build/proofs/boot-rom.png --expect-zxux-login'
```

Use the same Python executable in the FUSE command as in the main
release invocation. Adjust only the external file locations and make
sure the FUSE command is checked as required by the private checker.
A local `release/` directory must not already exist. The script refuses
a dirty checkout and stops at the first missing tool, failed test,
invalid capture, unchecked input or failed scan.

The entry point verifies external tool hashes, checks the source tree,
builds the system and the C48 runtime, checks 692 assembler forms, boots
the real ROM tape in the simulator, runs the system regression suite,
compiles 56 programs, performs native cassette sessions, checks native
and bytecode host-VM behavior, measures LM with the new compiler, runs
Hanoi and Queens8 concurrently, generates the gallery, and checks the
new tape in independent FUSE. It then checks generated files and copies
only approved files and a hashed manifest to `release/`.

The independent FUSE test must confirm the banner, console title and
`login:`; starting an emulator alone cannot pass. Historical old-kernel
visual comparisons are not part of this independently reproducible
release command. They must be assessed separately before claiming full
Step 5 historical visual closure.

## Files and verification

The release includes direct `.tzx`, `.tap`, `.ssx`, `.z80`, `.png` and
other approved program files, not ZIP-wrapped executables. Each manifest
entry records its size and SHA-256. Private tools and rules are excluded.
Never interpret an LM compiled file as proof that LM ran on the 48K.

The supplied `tools/release_v1_strict.py` remains a compatibility
launcher. `tools/release_v1.py` itself enforces FUSE argument validation
and independent proof verification, so no GitHub workflow or wrapper
is necessary to enforce the mandatory boot gate.

# ZX-UX v1: C48 build and screenshot proof

This page identifies the actual machines and programs shown in the
screenshots. No illustration or image lookup is used as test proof.

## System build

- Target: ZX Spectrum 48K; 64-column ZX-UX text, with 4-by-8 glyphs.
- Resident kernel: 8,191 bytes, within the 8,192-byte limit.
- Startup area: 165 bytes, within the 256-byte limit.
- Free arena after filesystem loading: 12,946 bytes.
- ROM tape boot: completed with SkoolKit 10.1 and the checked 48K ROM.
- System tests: 20 passed, zero failed (two batches).
- Assembler check: 692 instructions matched SJASMPlus 1.24.0.
- Standard C48 programs: 56 compiled from supplied SDK-side C source.
- FUSE boot: not run. Independent upstream SDK VM tests: not run.

The checked TAP, TZX, binary and snapshots are in `build/`.
The tested programs were rebuilt from `c48-sdk/usr/src/`.
The four pairs below use the same compiled SSX program in each runtime.

## ROM boot and multitasking

![ZX-UX v1 boot after a ROM tape load](../build/proofs/boot-rom.png)

The login screen was captured directly from the loaded 48K snapshot.
It uses ZX-UX's 64-column font, doubled in the PNG output.

![Hanoi and Queens8 on the emulated 48K Spectrum](../build/ZX-UX-multitask.png)

This is an actual Z80 multitasking snapshot produced with `tools/mtsnap.py`.
Hanoi and Queens8 use the checked multitask SSX variants, which were not
newly generated from the supplied C source for this picture.
The accompanying machine snapshot is `build/ZX-UX-multitask.z80`.

## Source-built C48 programs

Each left image is a real ZX-UX 48K emulation after tape loading.
Each right image is the ZX-UX SDK's host `rvm`, running the same SSX
program and Spectrum screen format. It is NOT a screenshot from the
separate upstream C48 SDK compiler and reference VM.

| Program and source | ZX-UX native runtime | ZX-UX SDK host VM |
|---|---|---|
| `examples/hello.c` | ![ZX-UX hello](../build/proofs/hello.ZX-UX.png) | ![rvm hello](../build/proofs/hello.rvm.png) |
| `games/fortune.c` | ![ZX-UX fortune](../build/proofs/fortune.ZX-UX.png) | ![rvm fortune](../build/proofs/fortune.rvm.png) |
| `demos/city.c` | ![ZX-UX city](../build/proofs/city.ZX-UX.png) | ![rvm city](../build/proofs/city.rvm.png) |
| `security/secforge.c` | ![ZX-UX secforge](../build/proofs/secforge.ZX-UX.png) | ![rvm secforge](../build/proofs/secforge.rvm.png) |

The freshly rerun native cases passed: `hello`, `fortune`,
`fortune:play`, `city` and `secforge` (5/5).
The host VM cases completed and produced their 6912-byte screen images.
The two display-text repairs to `fortune.c` and `secforge.c` were included.

## Reproduce

Use the private checked SJASMPlus, SkoolKit 10.1, the Spectrum 48K ROM,
and the compiled C48 runtime. Keep those private tools outside Git.

```sh
python3 tools/build.py /path/to/sjasmplus
python3 tests/test_boot_v1.py
python3 tools/mktapes.py --sdk /path/to/c48-sdk-source
python3 tests/ssxrun.py --only hello,fortune,city,secforge --png build/shots
python3 tools/c48_proofs.py
python3 tools/mtsnap.py 500
python3 tools/bootshot.py
```

Run the ROM tape loader to create `build/test.z80` before using the
snapshot-based screenshot commands. The separate upstream SDK reference
compiler and VM are not contained in the supplied `usr/src` archive.
An upstream SDK screenshot comparison was not run.

The LM `ailmzx48` source and unchanged cold model are in `c48-sdk/usr/src/`.
That program needs 21,010 bytes and cannot run as one process in the
12,946-byte free arena of the current build. There is no claim of an
on-device LM screenshot or working native LM program.

These files are checked build proof, not a complete final release.
The repeatable final release script stops when mandatory SDK or runtime
checks cannot be completed.

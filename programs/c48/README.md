# ZX-UX v1 C48 program sources

This directory holds the C48 sources used by the current `sdk/rcc`
compiler, cassette tests, and the standalone release script. The files
were copied without altering their source contents from the original
C48 program collection. They have no dependency on the retired compiler,
linker, executable formats or kernel.

The copyright and attribution notices embedded in individual files remain
applicable. See the repository `LICENSE` before redistributing software.

The `ailmzx48/` C and header files provide the LM new-compiler proof.
LM training/model assets are outside the normal v1 release and are not
needed to compile or measure the 48K loading limit. No native execution
of LM is claimed merely because its SSX1 output can be generated.

To compile the 56 C48 programs, run `python3 tools/mktapes.py` after
`python3 sdk/lib/build.py`. To run independent VM checks, use
`python3 sdk/tests/vm_reference.py --native` and `--bytecode`.

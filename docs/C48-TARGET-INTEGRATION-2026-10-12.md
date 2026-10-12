# ZX-UX C48 target checks

The C48 host compiler is `sdk/rcc`. The project owner confirms that another Windows C48 compiler is not required for v1.

The current verifier recorded 1,146 passing executions, no failures, and no errors. The scoped compiler gate passed.

The 20 target paragraphs are recorded in `tests/c48/matrix.json`. Each record includes its section number, test names, implementation paths, and review status.

Sixteen have supporting tests and source files. Three state implementation contracts. One remains partial: separate ARG1 and ENV1 process storage. The new direct IX witness is described below.

The earlier real ZX-UX emulator run covered 73 C48 cassette scenarios. The new SDK also compiled LM, but its image exceeds the tested native memory allowance. These runs are not a final clean-release test on the current source.

The existing full release gate remains active. The earlier historical frame comparisons are not confirmed state matches. No final v1 release is claimed.

## Native IX frame-register witness

The direct ABI witness `tests/c48/ix_abi_probe.py` assembled the unmodified current `sdk/lib/frame.asm` with the ZX-UX SSO1 assembler and linker, then executed nested calls on the checked SkoolKit 10.1 Z80 simulator. All eight initial IX/stack variants returned with the original IX and SP values.

The frame source hash is `b2814a1711868de329da6bb7968fe7b75bd3859d5e2721ef9ba21bcb913f0d6f`. This test covers the frame calls used by the witness. It does not prove that all v1 process paths work. The separate ENV1 check is still open.

Command (with checked toolbox on Python's import path):

```
python3 tests/c48/ix_abi_probe.py --report build/logs/ix-abi-proof.json
```

The independent compiler's previously verified 1,146 passing executions are retained; no additional case has been added to that verifier by this test. The full strict C48 coverage gate remains blocked.

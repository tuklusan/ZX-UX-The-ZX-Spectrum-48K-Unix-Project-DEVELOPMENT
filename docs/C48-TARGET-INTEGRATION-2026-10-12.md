# ZX-UX C48 target checks

The C48 host compiler is `sdk/rcc`. The project owner confirms that another Windows C48 compiler is not required for v1.

The current verifier recorded 1,125 passing executions, no failures, and no errors. The scoped compiler gate passed.

The 20 target paragraphs are recorded in `tests/c48/matrix.json`. Each record includes its section number, test names, implementation paths, and review status.

Fifteen have supporting tests and source files. Three state implementation contracts. Two need further proof: register IX preservation at a call boundary and separate ARG1 and ENV1 process storage.

The earlier real ZX-UX emulator run covered 73 C48 cassette scenarios. The new SDK also compiled LM, but its image exceeds the tested native memory allowance. These runs are not a final clean-release test on the current source.

The existing full release gate remains active. The earlier historical frame comparisons are not confirmed state matches. No final v1 release is claimed.

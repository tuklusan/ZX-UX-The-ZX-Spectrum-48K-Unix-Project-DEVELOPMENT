Dynamic DIM storage lacks a verified three-base native source build.

Original BASIC: `36-postman.bas`; SHA-256: `5754398693c6087dfdab78c65f6431caf66045e17e829482ff28988f499ed2cb`.

Original tape: `36-postman.tzx`; SHA-256: `af112fd1bbff766a07a8a2c4b3856e9dcc59af96bdd67f3f22db9a8bd68e1213`. Independent TZX extraction, strict ASCII conversion, token round-trip, and BAS/TZX line comparison succeeded.

- BAS compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

- TZX compilation: failed (exit 1); `RBC_NATIVE_BLOCKED ValueError: dynamic DIM budget has no three-base source witness yet`

No runnable native SSX is included. The default limit is 14,000 bytes; a successful assembler/linker alone does not prove execution.

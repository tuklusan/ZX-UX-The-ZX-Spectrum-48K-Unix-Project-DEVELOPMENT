# C48 source comments: byte exception

For ZX-UX v1, the C48 language specification permits any eight-bit
byte within line and block comments. A UTF-8 copyright symbol is valid
comment content, but not a C48 identifier, operator or literal character.
Lexical comment delimiters and physical LF boundaries are unchanged.
Outside comments, canonical source must still use the specified ASCII
bytes. Non-ASCII program data uses supported escapes.

The authoritative Rev 0.11 document updates paragraphs 39, 42, 44,
45 (a code-format listing), and 49. The test trace indexes all of these
except the code-format listing at 45. The updated document SHA-256 is
recorded in `tests/c48/traceability.json`, which is checked at runtime.

Run both compiler modes using `tests/c48/conformance.py`. The directly
mapped test batch is `tests/c48/spec_batch16_comments.py`. This change
clarifies allowed source comments; it is not a waiver of token rules,
compiler behavior, or the independent target/release verification gates.

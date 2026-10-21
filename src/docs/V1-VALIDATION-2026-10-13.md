# ZX-UX v1 native validation checkpoint (2026-10-13)

**Engineering verification checkpoint. Step 7 final release gate remains open.**

The approved `sdk/bin/rcc --native` compiled `tests/c48/native_env1_storage_lifetime.c`. The current C48 runtime archive was freshly rebuilt. Independent assembler/linker work reproduced the exact compiler-produced SSX1 file. The ENV1 symbol resides in the private BSS at image offset 1202. SSX1: 1317 bytes; required program memory: 1590 bytes.

Actual ZX Spectrum 48K execution from a ROM-loaded tape snapshot produced two separate foreground `C48-ENV1-OK` results. Free memory was 10322 bytes both before and after each run. During overlapping processes, slot 2 had image pointer 50738 and ENV1 value 90 while slot 3 had image pointer 52432 and ENV1 value 65. Both native paths reached their success markers. Free memory after both ended was 10358 bytes. Screens were captured at the observed frames; output may disappear when the console returns to the shell.

The rebuilt candidate tape also booted in real FUSE SDL 1.6.0. The checked 48K ROM and observed screen showed the ZX-UX banner, console title and `login:` prompt.

SHA-256: runtime archive `044c25c3fec3314f54daa7ce6fc0f25f1f8f769eaa3df2c370acff807a39f43b`; native SSX1 `616265f4ccd555204051a2c3c2a02807707ff47bba8a81c8e149aec55f29b60b`; rebuilt TZX `27471d1d37222ac77194fc1a08dfef4bd080dcfafd682c6d3148101d6ee4b95b`; tape-derived snapshot `d804a824bd16bbf3470ff0b1fbdf983400fd027cedcbacbd17c8a61e1a82d4e3`; FUSE capture `17df57187fff17cac3715a22a12731829cb2a692015833c7305dfe116ab9e764`.

**Scope limit:** this execution used a reconstructed subset of remote source, with individual relevant Git blobs verified; it did not use a complete clean current-HEAD Git checkout. The report does not satisfy that release requirement. Final strict language/target, entire integration corpus, LM, historical visuals, and clean release with independent FUSE proof remain mandatory. Do not infer missing tests passed.

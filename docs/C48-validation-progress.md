# C48 validation progress

The C48 Language Specification Rev 0.11 is published as a standalone document.

The saved new-SDK test report records 422 passing tests. The host C48 language group contains 157 tests. The saved source collection compiled 58 programs, including the large LM program. Compilation does not prove native execution.

Historical reference images are published for 24 demos, six examples, 14 games and four applications. Host renderings match the older SDK pictures for 27 cases with no pixel differences. The argv example has 728 differing pixels and is inconclusive because its historical capture state is not established. The other 20 reference cases have no approved host comparison.

The old-kernel native screen records are a separate dataset and are not substituted for SDK pictures. The matched host images are not proof of C48 execution on the current ZX-UX kernel.

Step 5 remains open for native language conformance and controlled native visual checks. Step 6 remains open for v1 program execution. Step 7 requires a fresh clean build and an actual FUSE boot of the tape built from that candidate. Step 8 release approval is not granted.

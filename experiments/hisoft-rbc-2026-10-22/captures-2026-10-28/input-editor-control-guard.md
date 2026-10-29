# Bounded ZX-UX INPUT cursor/edit guard — 2026-10-29

The original 48K ROM editor handles cursor and EDIT keys. The ZX-UX
terminal passes the four cursor keys as codes 8–11 and EDIT as 7.
The bounded source reader previously admitted cursor codes into its
printable-character path; that is not Sinclair cursor editing.

The source-level reader now **refuses** codes 7–11 by restoring its tty
mode and terminating the native process with status 1. It does not
pretend to move the cursor or edit an earlier character. A normal
printable line and DELETE still return status 0. This is a safety
repair, **not ROM INPUT equivalence**, and it does not authorize
making the ZX-UX input backend the compiler default.

Real ZX-UX emulator tests in `test_native_input_control_gate.py` checked
all four cursor keys and EDIT independently. Each refused with status 1,
released the screen, and restored the working shell prompt. The
printable/DELETE control completed with status 0 and the expected
screen attribute. Both tests passed. ROM syntax (6 tests), existing
native CLI (3 tests), and 34-game shadow admission units (2 tests) passed.

The six original INPUT-game BAS and independently converted TZX
sources each linked with native `ras/rld` under the default 14,000-byte
limit. All six pairs were byte-identical after the guarded source
change; 12/12 builds exited zero. Individual results are preserved only
under untracked `build/tmp/rbc-input-six-pairs/` and in the local
`build/tmp/rbc-input-six-pairs-control-refusal.log`.

The later full 34-game shadow replay was interrupted during batch 2
by the execution environment. The first five programs showed changed
screens and the sixth also did so, but **34/34 was not rerun to
completion with this change**. An independent complete 34-game shadow
pass exists on the preceding input version; it must not be reused as
proof of this new build.

Original BAS, TZX, published SSX, ROM, kernel, and release tape remain
unchanged. Production promotion is blocked until original ROM editor
control-key behavior and error handling can be supported and checked.

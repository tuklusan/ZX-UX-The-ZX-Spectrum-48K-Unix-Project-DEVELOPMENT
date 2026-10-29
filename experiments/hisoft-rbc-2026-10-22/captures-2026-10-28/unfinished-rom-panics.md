# Three unfinished published games: original ZX-UX ROM-error panic

Three source-guided native runs found a concrete blocker, not a finished round. The original `03-tug-of-war`, `43-dogfight`, and `47-exocet` SSX files, without rewriting or relinking, each reach the actual ZX-UX kernel's `rom_error` entry and then its `panic` entry. The code at `src/zx-ux/unix.asm` routes a ROM RST 8 error to the panic loop. That loop clears screen ownership and disables interrupts. A blank screen or missing owner therefore must **not** be described as game completion, clean STOP, or normal shell return.

The independently recovered 48K ROM, kernel, source programs, and linked executables were not edited. A read-only instruction hook returns `False` to run the real instruction. The hook records the two entry points while the ZX-UX Z80 executes; it never patches the machine, program, memory, CPU registers, game data, or pixels. Each linked SSX passes both unchanged 14,000-byte admission checks. The rebuilt `build/out/ZX-UX.tzx` matches the frozen release byte-for-byte.

| Original published game | Source-guided real key | ROM-error and panic machine frame | Published SSX SHA-256 |
| --- | --- | ---: | --- |
| Tug of War | `a` after the instruction screen | 1000 | `e12b891fda3b97f0f53ea1c45f8c97caa9115b07f084bfd8d50aa271ff9f3294` |
| Dogfight | `a` after the instruction screen | 1513 | `ccea6b421d27023e54590892f2f1350d6f53559ad6f15ba68b59567222cf8a31` |
| Exocet | `a` after the instruction screen | 1611 | `ed308cf3e60bc90cf4b17c5bb6ff5b66f05faf3980ec8eeefc0743885f9ff921` |

The machine frame numbers belong to this exact cached-boot run, not universal timing guarantees. At the error point, `rom_error=0x6060` and `panic=0x6048` were read from the rebuilt kernel symbol file. After the panic, the real CPU reaches the interrupt-disabled HALT loop at `0x605E`; the foreground job remains without an exit record even though the kernel no longer grants it screen ownership. No game-over, replay, or user exit was observed in these runs. The fault's deeper cause has **not** been identified; the ROM-error entry alone does not prove which BASIC operation caused it.

Repeat from repository root after rebuilding the original kernel metadata and historical RBC font:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_unfinished_rom_panic_diagnostics.py -v
```

The three-case native test passed as a **failure detector**, not a gameplay pass. Earlier bounded probes remain valid observations; this narrows down the lost-screen question for these three programs. The overall published set stays at 120 original inputs, 34 SSX and 26 README files. Full-round coverage stays **23/34**, with **11** unfinished. Nothing about this negative result authorizes changing a game source, patching an SSX, or weakening the loader.

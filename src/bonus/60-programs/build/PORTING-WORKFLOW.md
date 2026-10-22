# BASIC-to-C48 workflow — v0.4

Applies to **all 60 numbered ZX Spectrum BASIC programs**, whether games, utilities, educational software or other applications. Work in historical order (01–60). The port must reproduce the *actual* BASIC program; a similar-looking replacement is not a port.

**Non-negotiable:** ZX-UX `beta-0.2.0` is frozen. Only `src/bonus/60-programs/` is writable. Never edit original `BASIC/` files, the SDK/compiler/kernel, the emulator, the root build/release process or `dist/`. Use the frozen tools in the permitted workspace or disposable copies. GitHub `main` is permanent storage; verify its live HEAD before changes and pushes.

From `src/bonus/60-programs/`, `NN-name` denotes any numbered program directory. All new port sources, final SSX/TZX tapes, genuine captures and brief notes go in `NN-name/C48/`. Shared 8×8 renderer, VGA font and interface are under `c48lib/`; scripts are under `build/`. `build/tmp/` is scratch space, with only `.gitkeep` tracked.

## Port once, then test

1. **Read the whole BASIC program and its references.** Open `BASIC/NN-name.bas`, original tape, existing screenshots, README and replay/timing notes. Work through every line, BASIC `DATA` value, control, formula, screen operation, input, sound and state transition. Record a short BASIC-to-C48 routine mapping in `C48/README.TXT`. Check against genuine original behavior; regenerated tapes from `build/build-basic.py` are secondary references, **not** byte-identical historical tapes.
2. **Translate faithfully.** Implement `C48/stem.c` (tape name at most ten characters). Use only verified frozen SDK APIs. Where needed, put the game's own sprite bytes in `C48/stem-glyphs.asm`, transcribed and independently checked against BASIC `DATA`/`POKE` order. Use `c48lib` for 32×24 full-height text/glyphs. Do not maintain generated `stem.asm` in Git. Record necessary differences without disguising defects as differences.
3. **Check behavior and keyboard semantics.** `INKEY$` observes *current* keys; terminal `getchar()` can consume stale buffered input. Test idle, held keys, quick taps, shift combinations and fresh-key prompts as applicable. Prevent terminal echo onto the screen. For non-game programs, test their real calculations, validation, strings, output and error paths instead of inventing game tests.
4. **Build and run.** `python build/build-c48.py NN-name` compiles/links with the frozen SDK, generates SSX/TZX and cleans generated assembly from `build/tmp/` after success. Boot the actual frozen ZX-UX kernel, execute the port, and test representative normal, error, boundary, completion and restart paths. Compare equivalent states with the original BASIC. Existing `build/test-c48.py` currently tests **only programs 25 and 58**; add relevant regression checks for other ports. Running SSX directly does **not** verify `yolo` loading.
5. **Check for leftovers.** Inspect drawing/erasing source paths and successive real emulator frames. Every moving, deleted, overwritten, scrolled, flashed or cleared screen item must restore its former pixels **and attributes** correctly. Look for trails, ghost text, stray glyphs, stale scores, color remnants and edge clipping that BASIC did not leave. Include negative redraw cases; use real captures, not invented pictures. If the program never updates the screen, explain why the check is not applicable.

## Mandatory independent review loop — three clean rounds

This is a **repeatable gate**, not three rubber stamps. Start each round with **fresh disk bytes**, not memory or only diff hunks:

- **Step 1 — scan:** Reopen the latest BASIC and C48 source files from disk, including local glyphs, relevant shared code and data. Inspect the full file bytes manually, line by line. The gate fingerprints these bytes to detect later changes.
- **Step 2a — independent normal review:** Compare the C48 source and actual runtime results against BASIC, branch by branch, including calculations, inputs, layout, sound and the leftover-pixel check where applicable.
- **Step 2b — independent adversarial review:** Try invalid/boundary inputs, prolonged/repeated keys, collisions, overlapping redraws, extreme values, restarts and all applicable exceptional paths. Prefer a separate reviewer/agent when available; never claim one if absent.
- **Step 3 — any gap:** Fix **C48 only**, add a test, rebuild and rerun. Reset the clean count to **zero**; start again from Step 1 on the newest disk bytes. Unfixable defects are blockers, not exemptions.
- **Step 4 — release threshold:** Finish only after **three successive full Step-1 scans**, each followed by clean 2a and 2b reviews, with zero outstanding defects. Even three clean rounds do not prove an untested runtime feature.

## One short checklist record, no duplicate paperwork

Use the existing `C48/README.TXT` for the mapping, actual findings, tests, departures and open issues. The **only additional signoff file** is the automatically initialized `C48/PORT-CHECK.json`:

```sh
python build/check-c48.py --init NN-name
```

- In `checks`, mark each applicable manual item `PASS` **only after doing it**. Four conditional items (`inputs`, `remnants`, `yolo`, `checker`) may instead use `"N/A: reason"` when truly inapplicable. `NOT_RUN` and `FAIL` block completion. One concise README serves as the human review note; **no separate attachment or hash spreadsheet per checkbox**.
- Set `known_defects` to `[]` **only when there are none**. Add an `audits` entry for each genuinely completed scan/review round. The script supplies `source` during `--init`; reuse that exact digest **only while the disk bytes remain unchanged**. For example (illustrative, not a completed review):

```json
{"round":1,"source":"<digest from checklist>","scan":"PASS",
 "normal":"PASS","adversarial":"PASS","reviewer":"actual reviewer",
 "note":"what was inspected and challenged","defects":[]}
```

- If any defect or source change occurs, run `python build/check-c48.py --restart NN-name` after the repair; this resets **all** checkmarks and all three audit rounds. Git history retains older records, so the JSON does not accumulate a duplicate history archive.

### Fail-safe stop checks

```sh
python build/check-c48.py NN-name             # required before push
python build/check-c48.py --closeout NN-name  # required after push
```

The gate **prints every one of its 21 checklist items** and exits nonzero if any required status or audit is missing, the source digest is stale, three clean rounds are absent, the SSX/TZX is invalid, the rebuilt bytes differ, `build/tmp/` is dirty, or Git scope checks fail. It performs **two fresh builds itself**; no separately maintained rebuild-hash ledger is needed. Only the remote read-back may remain PENDING at the pre-push stage.

After `PREPUSH READY`, read live remote `main`, reconcile changes, inspect the **complete** Git diff (including removals/renames), and reject every change outside `src/bonus/60-programs/` or any unrequested original BASIC change. Run the available private checker, fast-forward commit/push without modifying tags, and read back remote HEAD and changed paths. `--closeout` must report **CLOSEOUT COMPLETE** against that live commit; otherwise delivery remains open. When Git/network access is missing, it fails rather than inventing a result.

**The mechanical guarantee is that all 21 registered checks are evaluated and missing/stale records are rejected. No script can guarantee someone honestly read every line; independent reviews must actually happen.** Report translated / compiled / linked / packaged / ZX-UX executed / visually compared / adversarially reviewed / `yolo` loaded separately, with NOT RUN for any untested claim.

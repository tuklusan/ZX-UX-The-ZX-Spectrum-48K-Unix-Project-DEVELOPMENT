# ZX-UX original Sinclair BASIC collections

## Closed collections — 31 October 2026

The Granada Publishing and Spectrum Show sets are **closed**. Every distinct program in their checked source inventories has a folder on live `main`. No further processing is scheduled for either set.

| Collection | Program folders | Remaining |
|---|---:|---:|
| Granada Publishing | 24 | 0 |
| Spectrum Show | 73 | 0 |
| Numerical Analysis (F77S, closed earlier) | 20 | 0 |
| **Total** | **117** | **0** |

These counts mean the source folders were processed and published. They do **not** mean every game was won or every tape yielded a stand-alone BASIC text listing. The original archive counts were checked as working inventories; identify new or duplicate source items before changing a total.

Known limits remain visible in the game folders:

- **Amaze:** 49 BASIC lines checked locally; its separate text listing was withheld after the private checker rejected it. Original media and real Fuse play captures are committed.
- **Outlander:** 149 physical BASIC records were checked, including four records numbered zero. Repeated line numbers prevent a strict listing. Original media and real Fuse play captures are committed.
- **DungeonFinal, part 2:** the second tape program is present as `43-dungeonfix-DungeonFinal-02`, with 531 BASIC lines, a 68-line graphics loader and Fuse map-play captures. The complete quest was not proved.

The old sets are finished. This guide stays here for the next collection; no new collection is active.

## When a new collection arrives

1. **Get the inputs.** Obtain the new original archive, access to live GitHub `main`, the private checker, and the needed emulator tools. Read the complete `english-writing-rules for-technical-manuals.txt` and `Github Remote Repo Commit + Push Procedure used for ZX-UX v1.txt`. Read current repository sources and tests. Start from the live tree, never an old ZIP or remembered commit.
2. **Sort the originals.** Inspect archive members safely; reject unsafe paths and links. Separate distinct programs, duplicate names, multi-part tapes, BASIC, machine code and non-program items. Keep original media bytes unchanged. Use a new `src/assets/basic-src/original-sinclair-basic-collections/<collection>/<program>/BASIC/` folder for each distinct program. Leave `bin/` empty; Git needs no placeholder.
3. **Check the listing.** Inspect manuals and original screenshots. Recover BASIC only from a real BASIC source, using `build/tools/zx-tzx2bas.py` and the repository's 48K ROM where suitable. Independently check the numbered lines and token data. Label a missing, mixed or rejected listing plainly. Never invent or repair original source to force a pass.
4. **Run and record.** In genuine Fuse 48K, reach actual gameplay where possible and try at least two documented key actions. Save genuine before/after game views in `BASIC/SCREENSHOTS/`; check the pixels, not just the filenames. Supply a repeatable `REPLAY.sh` with key holds and waits. If play fails or the screen change could be idle motion, say so. Archive reference images are not Fuse captures.
5. **Keep short game notes.** Add `README.TXT` with the source media, listing result, actual play and limits; add `KEYS-AND-TIMING.txt` with observed keys and timing. Check preserved source bytes against the input archive. Do not create native SSX output or change the old collections, SDK, RBC, distribution or unrelated files.
6. **Test and publish each program.** Run only affected checks, the private checker self-test at session start, and its full four-attempt pre-write check on all proposed text, paths, commit message and exact push command. Stop on rejection. Re-read the live branch head and tree, then make one fast-forward commit for the program **and this status guide together**. Follow the supplied GitHub push procedure. Read the branch and changed files back before counting the program as done.

For each new set, keep only the current done/remaining count, the next program and any real blocker in this file. At zero remaining, mark that set **closed**. We do not need a history of every keystroke here; the game folders already have it.

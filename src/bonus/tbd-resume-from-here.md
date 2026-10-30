# ZX-UX bonus BASIC collections — resume here

## FIRST ACTION IN A NEW CHAT: REQUEST THE INPUTS

**Do not start editing, running games or pushing until these inputs are available in the new chat.** Ask the user to provide or confirm access to:

1. **Live GitHub repository and write connection:** `tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT`, branch `main`. Read the live HEAD, tree, relevant source and scripts. Never treat the old repository ZIP as live state. Earlier checkpoint: `757e99727ac670e89da41a91b87d646a632d352a`. Later work is listed below. Check the current HEAD; no saved SHA is an expected future HEAD.
2. **Original collection archives:** `F77S_TO_ZX_BASIC_20_ROM_VERIFIED.zip`, `Granada-Publishing.zip`, and `www.thespectrumshow.net.zip`. The archives include source media, original listings and, for Spectrum Show, reference screenshots. Ask for fresh attachments if unavailable; do not infer missing bytes from previously committed derivatives.
3. **Mandatory repository write instructions:** read **all** of `Github Remote Repo Commit + Push Procedure used for ZX-UX v1.txt` before any GitHub write, including restrictions on staging, verification and force-free branch advances.
4. **Project rules and source tools:** obtain the ZX-UX project instructions in this document and inspect live `src/bonus/60-programs/` and `build/tools/zx-tzx2bas.py` (verified TZX/ROM LLIST), the live Fuse/replay tools and tests, and `src/zx-ux-sdk/rom/48.rom`. Use repository tools in preference to reimplementing them.
5. **Emulation environment when missing:** Fuse 1.6 SDL, Xvfb, Python 3, Pillow, `python-xlib`, and any documented repository replay dependencies. Existing supplied packages include `fuse-emulator-sdl_1.6.0+dfsg1-2+b1_amd64.deb`, `fuse-emulator-common_1.6.0+dfsg1-2_all.deb`, `libspectrum8_1.5.0-4+b2_amd64.deb`, `libsdl1.2debian_1.2.68-3_amd64.deb`, and `libaudiofile1_0.3.6-7+b2_amd64.deb`. Install only what is actually missing. Do not invent a completed emulator run.
6. **Optional reference material only:** `ZX-UX-GITHUB-REPO-25d31dd8352c6417b05441ef620708fe9765a7b9-BEFORE-ADDING-3xBASIC-SETS.zip`, `ZX-UX-48K-toolbox.zip`, `english-writing-rules for-technical-manuals.txt`, and `POST-RBC-PACKAGING.md`. The packaging task is **not** being resumed; RBC is already complete and packaged.

If any required archive, source, tool or permission cannot be accessed, identify the missing item. Do not quietly substitute generated content, old snapshots, or unverified screenshots. Otherwise proceed autonomously, with minimal narration, and stop only for an actual blocker.

## Writing rules for every English text

Before writing or editing any English prose, **read the complete** `english-writing-rules for-technical-manuals.txt` from the project sources or the supplied original file. The file is a required input in each new chat, on the same footing as the ZIPs and GitHub push steps. If it cannot be read, request it before writing prose or proceeding with game notes.

Apply **all** its English writing rules. This includes accurate source-based claims, the SANYALnet Labs voice, the specified pronouns, plain language, the required dry humor, sentence flow, and the rules against repeated or stock prose. Follow its **entire blocked-word and blocked-phrase list**, including the extra entries at the end. Never insert any blocked term into newly written English. Check finished text before staging it.

These rules apply to every new or edited README, gameplay note, key list, timing guide, screenshot caption, replay comment written in English, Git commit message, progress report, and resume guide. They also apply to user-facing English updates. Do not copy blocked terms into prose merely to explain that they are blocked. Keep original media, quoted BASIC source, filenames, code syntax, test data, and existing third-party text unchanged; do not damage source bytes to enforce a prose rule.

Write each game note only from original input, live code inspection, direct Fuse play, and visible screen results. No guessed controls or gameplay. Recheck the rules for each batch, before any GitHub write. The Spectrum has enough surprises without invented instructions.

## Scope and standing decisions

Add **three separate bonus collections** alongside, and without modifying, the existing 60-programs collection:

- `src/bonus/F77S_TO_ZX_BASIC_20_ROM_VERIFIED/`
- `src/bonus/Granada-Publishing/`
- `src/bonus/www.thespectrumshow.net/`

Use one directory per distinct original program; within each game use `BASIC/` and `bin/`. Git does not track an empty `bin/`; **do not add a placeholder**. Do not compile, package, or publish native SSX output for these new games. Do not edit existing 60-program media, SDK, RBC, ROM, C48, distribution, release assets, or unrelated files. Do not create extra branches, tags, ledgers, optimizer or reports. No source or media rewriting to make a program compile.

**Private checker is enabled by owner request on 2026-10-30.** Run its private pre-write workflow before every GitHub write. Run other *applicable*, affected tests and ROM/listing/emulator checks. A past private checker complaint about an unrelated RBC license file is not authorization to edit RBC. Preserve all unrelated experiments.

**Anti-bureaucracy:** minimal and sufficient direct work; work on up to **12 games in parallel** for analysis and genuine local emulation where resources allow. Finish and **push at every program boundary** to avoid loss if the local container disappears. Parallelize preparation and file uploads but serialize commits/ref updates against the exact newest live HEAD; do not push concurrent commits against a stale parent. No narration or prompts between routine steps.

## Continuous restart status — required at every program push

This file is the single restart point. Update it **in the same commit** as each finished program, not in a later housekeeping commit. Record the program name and media checked, actual BASIC listing result, Fuse play and image result, applicable test result, private checker result, completed and remaining counts for each collection, the next program to try, and any unresolved game input. Keep the total based on distinct program folders on live `main`, with the archive total labeled preliminary until the source set is fully checked.

The last successful remote readback is the only completed checkpoint. Before a new push, record the exact live parent HEAD and tree and compare the changed paths. After the push, read back the new HEAD, tree, paths, and files. On the next program, replace the earlier checkpoint with the new checked state. Never write a predicted future commit ID. If work stops between commits, restart from live GitHub and retest any local-only work. Do not count an unpushed game. Preserve the original media and all unrelated source bytes.

The private checker is enabled by owner request on 2026-10-30. Run its self-test when starting a new session. Before **every** GitHub write, check the complete proposed text, paths, full commit message, and exact push command with the private four-attempt workflow. Keep private checker files outside Git. If the checker rejects a change, stop that write after the allowed checks; do not weaken rules or publish the blocked content. Keep the writing rules in force for all new English prose. Run the other tests that apply to the game. Do not claim a passing run without running it.

## Progress at pause — committed program directories

**58 / 117 (49.6%) complete; 59 remaining (50.4%).** Counts reflect program directories present on live `main` when this resume file was updated, against the preliminary 117-program archive inventory.

| Collection | Done | Remaining | Total |
|---|---:|---:|---:|
| F77S | 20 | 0 | 20 |
| Granada Publishing | 8 | 16 | 24 |
| Spectrum Show | 30 | 43 | 73 |
| **Total** | **58** | **59** | **117** |

The 24 Granada and 73 Spectrum Show totals are **preliminary source-archive counts**. Recheck duplicates, non-BASIC items, distinct identities and actual gameplay proof before treating these as final. A committed directory is not automatically proof of a fully playable game. Bobsleigh, Fruit Machine, Commando Jump, Spectrum Invaders, Laser Attack, and Mighty Missile now have original media, checked listings, and live Fuse play samples on `main`. Their `bin/` areas have no native output. The progress baseline for a new chat is the latest live GitHub tree, not this frozen table.

## Exact pause point — verified GitHub state

The latest checked `main` before this guide update is:

`349d26db146b318b809d9c2620eb2d786a278874` — **Granada Mighty Missile**. We checked the unchanged original TAP, matching BASIC from its TZX copy, and two live Fuse key moves. Check the live HEAD again when work resumes. If it has moved, read the new files first; never overwrite other work.

Previously completed on remote:

- **F77S: 20 of 20 programs.** Original TZX, independently decoded LLIST `.bas`, notes and Fuse captures/replays are committed. Some are numerical demonstrations rather than games; do not relabel execution as human gameplay. No native SSX.
- **Spectrum Show: 30 program directories committed** at pause (not all 73 source entries). The initial 7 were replayed again from actual game starts after the user rejected title-screen-only captures. Programs 08–18 were added with hands-on replay and moves. Subsequent committed indices: **20, 21, 23, 24, 25, 27, 28, 34, 35, 36, 46, 48**. Missing index numbers are **not proof of missing programs**: inspect the archive and compare unique program identities and committed paths. Some entries may be duplicates, non-BASIC or not playable; record such findings truthfully. In particular, Outlander was flagged for LLIST rejection while media and actual Fuse gameplay were preserved. Never fabricate an LLIST listing.
- **Granada: 8 of 24 initially inventoried game directories:** `01-across-the-ravine`, `02-capture-the-quark`, `03-bobsleigh`, `04-fruit-machine`, `05-commando-jump`, `06-spectrum-invaders`, `07-laser-attack`, and `08-mighty-missile`. The last six have new checked tape copies, BASIC listings, notes, playable Fuse sessions, replay scripts, and screen captures. Original TAP bytes were preserved. `Noughts and Crosses` was examined locally, but its quoted row/column entry did not reach a confirmed move; **no files were pushed** for it. Try again from its original TAP and check the string input before making claims. `Guideline` has two source versions; determine whether they are distinct games before publishing. The 24 Granada and 73 Spectrum Show totals are early ZIP folder counts; review each source before final counting.

**No uncommitted local work should be assumed to survive.** The old container had temporary probes, transfer JSON files and images; those are not proof of remote publication and may be gone. Look at live GitHub first. Re-run unfinished work from the original archive, not an unverified old screenshot.

## Per-program workflow — use this exactly, and repeat

1. **Discover and classify.** Inventory ZIP members without extraction outside a temporary directory; reject path traversal/symlinks. Locate the distinct game/program and all relevant originals (`.tzx`, `.z80`, `.tap` where that is the actual original). Check names, duplicate identities and SHA-256 hashes. Identify whether the original contains Spectrum 48K BASIC, machine code, multiple parts or a nonplayable sample. Do not call every snapshot a BASIC source.
2. **Read first.** Inspect any included `.bas`, tokenized BASIC, program description, manual, key mapping and source screenshots. **Look at the supplied archive's reference screenshots** to learn the expected game screen, but do **not** copy them and call them Fuse captures. For `.z80` media, preserve snapshot bytes, identify any resident BASIC by independent ROM-aware decoding only when legitimately present. For `.tap`, preserve original TAP bytes as appropriate and produce an explicitly labeled derived TZX *only* when the conversion is verified. Preserve original TZX when supplied, unchanged.
3. **Prepare the `BASIC/` sources.** Use the *existing* `build/tools/zx-tzx2bas.py` (or repository-verified LLIST path) to decode original TZX; check lines, strings, REM, controls, glyph escape syntax, line ordering, and original token bytes independently. For source snapshots or non-BASIC media, mark the listing as unavailable if no trustworthy BASIC exists. Do not substitute the archive `.bas` as independent tape proof and do not manufacture BASIC lines. Keep media intact. Avoid redundant duplicate source copies unless necessary to distinguish original TAP, derived TZX and regenerated listing.
4. **Understand actual gameplay.** Read instructions and inspect the genuine original startup state in Fuse 48K. Determine keyboard controls from source, original on-screen instructions or observed behavior; do not guess. Confirm start/menu keys, delays, speed setting, and transition to the **actual game**, not a loader, intro, title, HELP screen, frozen menu, or emulator desktop.
5. **Play a couple of moves.** Run the original media in genuine Fuse (normally `fuse-sdl --machine 48` using an original `.z80` snapshot, or load the verified original tape), under Xvfb if required. Start the game and send at least two meaningful, documented key actions as a human player would—e.g. left/right, turn/move/fire—allowing enough time to see a game-state change. Where game mechanics prevent a reliable move, say precisely why. Screenshots may show a successful state change but must not be misrepresented as a full playthrough or compiled-native output.
6. **Capture and replay.** Save genuine Fuse captures under `BASIC/SCREENSHOTS/` (at least a gameplay-state image and a post-move gameplay image where playable). Use `BASIC/REPLAY.sh` or `REPLAY*.sh` with a reproducible startup, explicit timings, key holds, capture names and any necessary documented dependencies. Verify screen content by inspecting images, not by checking PNG existence alone; check that the second view actually reflects action rather than idle animation. Beware fixed cropping (e.g. 320×240 crop from an 800×600 Xvfb window) unless visually confirmed for that Fuse configuration.
7. **Document what was observed.** Under `BASIC/`, write `README.TXT` (identity, original/derived media, sha256 source hashes, BASIC listing status, gameplay synopsis, proof limitations), `KEYS-AND-TIMING.txt` (source/observed keys, start sequence, exact waits/holds), replay scripts, and screenshot origin. For undecodable, non-BASIC, blank or unplayable items, flag that explicitly rather than claiming success. Keep `bin/` empty for future native builds.
8. **Validate only relevant things.** Check original media bytes/hashes against input ZIP, listing parser output and line data, syntax without executing when applicable, replay exit status, genuine images, changed game state and script reproducibility; rerun only affected repository tests. The private checker is enabled. Run its private pre-write workflow before every GitHub write. Do not perform RBC/native compile or broad unrelated corpus tests.
9. **Commit and push after this program.** Re-read the entire supplied remote push procedure if starting a new chat. Check live `main` HEAD/tree immediately before writing. Compare exact changed file paths, modes and content. Prefer ordinary `git push` fast-forward. If network Git is unavailable, use GitHub Git Data API: create hash-verified blobs (inline UTF-8 or Base64, transferring bytes via Library when necessary), build a tree from the *current* live tree, verify full expected tree including unrelated files, create **one commit per completed program** with current HEAD as its only parent, `update_ref(force=false, expected_sha=current_HEAD)`, and read back HEAD/commit/tree/blobs. If HEAD moved, reconcile using the actual latest HEAD, never force. Remove temporary Library uploads after successful readback. A created commit object is not a pushed branch update.
10. **Move to the next program automatically.** Run a batch of up to 12 independent work items in parallel where feasible, but checkpoint each completed item remotely before proceeding. No prompts or busywork unless a real blocker needs user input.

## Where to resume concretely

**First:** check the required inputs in the first section, read the English writing guide, and check live `main`. **Next:** choose the next untouched Granada source folder from `Granada-Publishing.zip`. `Noughts and Crosses` has a playable board at startup but needs a working, quoted two-digit input before any move can be claimed. `Laser Attack` and other unopened folders are also ready for first inspection. Do not repeat the six Granada directories already pushed.

In parallel, compare remaining Spectrum Show originals with the live `src/bonus/www.thespectrumshow.net` tree. Process up to 12 independent game checks where practical, but push each completed program separately. Every published capture must come from actual input-driven Fuse play. Preserve all prior `60-programs` and other source bytes.

## Required remote readback / final state

At any stopping point, check latest `main` SHA and the changed-path list since the starting HEAD; confirm only intended `src/bonus/` files changed and original media hashes match. Report the number of distinct programs genuinely completed, cases explicitly unverified, remaining work, and latest verified commit SHA. Never claim a full collection, complete gameplay, or a pushed file without direct proof. The private checker is enabled and required before every GitHub write.
#!/usr/bin/env python3
"""Fail-closed BASIC->C48 port checklist, with minimal one-file signoff.

Run from src/bonus/60-programs:
  python build/check-c48.py --init NN-name
  python build/check-c48.py NN-name             # before push
  python build/check-c48.py --closeout NN-name  # after push
  python build/check-c48.py --restart NN-name   # after a defect or source edit

Manual judgments need one status per item and one review note in the program's
C48/README.TXT. The gate itself checks files, hashes, builds and Git state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
LABELS = (
    ("basic", "Original BASIC bytes reviewed"),
    ("mapping", "BASIC-to-C48 mapping complete"),
    ("references", "Genuine BASIC reference states checked"),
    ("sdk", "Only frozen SDK interfaces used"),
    ("data", "Data, formulas and optional glyphs checked"),
    ("inputs", "Input and terminal behavior checked"),
    ("link", "Frozen compiler and linker produced SSX"),
    ("tape", "Valid TZX and internal executable name"),
    ("runtime", "Actual ZX-UX runtime checked"),
    ("comparison", "BASIC/C48 behavior and screen compared"),
    ("remnants", "No unexplained leftover pixels, text or attributes"),
    ("negative", "Adversarial/negative behavior tested"),
    ("audit_1", "First fresh-byte scan + normal/adversarial reviews"),
    ("audit_2", "Second fresh-byte scan + normal/adversarial reviews"),
    ("audit_3", "Third fresh-byte scan + normal/adversarial reviews"),
    ("streak", "Three consecutive defect-free audits"),
    ("repro", "Two byte-identical frozen builds"),
    ("yolo", "yolo loading, if claimed"),
    ("hygiene", "Only authorized files changed; tmp clean"),
    ("checker", "Private checker result, if available"),
    ("remote", "Remote HEAD and committed bytes verified"),
)
AUTO = {"link", "tape", "audit_1", "audit_2", "audit_3", "streak", "repro", "hygiene", "remote"}
CONDITIONAL = {"inputs", "remnants", "yolo", "checker"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(folder: Path) -> str:
    """One fingerprint for *all* current BASIC and C48 source disk bytes."""
    paths = [p for p in (folder / "BASIC").rglob("*") if p.is_file()]
    for place in (folder / "C48", ROOT / "c48lib"):
        paths.extend(p for p in place.rglob("*") if p.is_file()
                     and p.suffix in {".c", ".asm", ".h", ".py"})
    paths.extend(ROOT / "build" / n for n in
                 ("build-c48.py", "check-c48.py", "test-c48.py"))
    h = hashlib.sha256()
    for p in sorted(set(paths)):
        if p.is_file():
            h.update(p.relative_to(ROOT).as_posix().encode() + b"\0")
            h.update(bytes.fromhex(sha(p)))
    return h.hexdigest()


def command(args, cwd, timeout=60):
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None


def git_errors(folder: Path, closeout: bool) -> list[str]:
    top = command(["git", "rev-parse", "--show-toplevel"], folder)
    if not top or top.returncode:
        return ["Git checkout unavailable"]
    repo = Path(top.stdout.strip()).resolve()
    if (repo / "src/bonus/60-programs").resolve() != ROOT.resolve():
        return ["not the expected repository checkout"]
    status = command(["git", "status", "--porcelain", "--untracked-files=all"], repo)
    if not status or status.returncode:
        return ["Git status unavailable"]
    errors = []
    for line in status.stdout.splitlines():
        for name in line[3:].split(" -> "):
            name = name.strip('"')
            if not name.startswith("src/bonus/60-programs/") or "/BASIC/" in name:
                errors.append("unauthorized working-tree path: " + name)
    if not closeout:
        return errors
    if status.stdout.strip():
        errors.append("uncommitted work at closeout")
    local = command(["git", "rev-parse", "HEAD"], repo)
    remote = command(["git", "ls-remote", "origin", "refs/heads/main"], repo, 30)
    if not local or local.returncode or not remote or remote.returncode or not remote.stdout.strip():
        return errors + ["live GitHub remote read-back unavailable"]
    commit = local.stdout.strip()
    if commit != remote.stdout.split()[0]:
        errors.append("local HEAD differs from live origin/main")
    diff = command(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], repo)
    if not diff or diff.returncode or not diff.stdout.strip():
        errors.append("cannot inspect committed changed-path list")
    else:
        for name in diff.stdout.splitlines():
            if not name.startswith("src/bonus/60-programs/") or "/BASIC/" in name:
                errors.append("unauthorized committed path: " + name)
    wanted = [folder / "C48" / "PORT-CHECK.json", *(folder / "C48").glob("*.c"),
              *(folder / "C48").glob("*.ssx"), *(folder / "C48").glob("*.tzx")]
    for p in wanted:
        name = p.relative_to(repo).as_posix()
        tracked = command(["git", "ls-files", "--error-unmatch", name], repo)
        match = command(["git", "diff", "--quiet", "HEAD", "--", name], repo)
        if not tracked or tracked.returncode or not match or match.returncode:
            errors.append("not committed at verified HEAD: " + name)
    return errors


def tape_stem(data: bytes) -> str:
    if not data.startswith(b"ZXTape!\x1a") or len(data) < 15:
        raise ValueError("not a TZX file")
    pos = 10
    if data[pos] == 0x30:
        pos += 2 + data[pos + 1]
    if pos + 5 > len(data) or data[pos] != 0x10:
        raise ValueError("executable tape block missing")
    length = int.from_bytes(data[pos + 3:pos + 5], "little")
    block = data[pos + 5:pos + 5 + length]
    if len(block) != length or len(block) < 13 or block[:2] != b"\x00\x04":
        raise ValueError("executable tape header invalid")
    return block[2:12].decode("ascii").rstrip()


def build_twice(folder: Path, sdk: Path | None) -> list[str]:
    sources = list((folder / "C48").glob("*.c"))
    if len(sources) != 1:
        return ["expected exactly one C48 source"]
    binaries = [sources[0].with_suffix(s) for s in (".ssx", ".tzx")]
    before = {p.name: sha(p) for p in binaries if p.is_file()}
    if len(before) != 2:
        return ["missing submitted SSX or TZX"]
    args = [sys.executable, str(ROOT / "build" / "build-c48.py")]
    if sdk is not None:
        args += ["--sdk", str(sdk)]
    args.append(folder.name)
    for index in range(2):
        r = command(args, ROOT, 180)
        if not r or r.returncode:
            return ["frozen build %d failed or timed out" % (index + 1)]
        result = {p.name: sha(p) for p in binaries if p.is_file()}
        if result != before:
            return ["build %d changed SSX/TZX bytes" % (index + 1)]
    return []


def clean_rounds(record, source: str) -> int:
    rounds = record.get("audits", [])
    if not isinstance(rounds, list):
        return 0
    streak = 0
    for index, rnd in enumerate(rounds, 1):
        if not isinstance(rnd, dict):
            streak = 0
            continue
        ok = (rnd.get("round") == index and rnd.get("source") == source
              and rnd.get("scan") == "PASS" and rnd.get("normal") == "PASS"
              and rnd.get("adversarial") == "PASS" and rnd.get("defects") == []
              and isinstance(rnd.get("reviewer"), str) and bool(rnd["reviewer"].strip())
              and isinstance(rnd.get("note"), str) and len(rnd["note"].strip()) >= 12)
        streak = streak + 1 if ok else 0
    return streak


def check(folder: Path, record: dict, sdk: Path | None, closeout: bool) -> bool:
    failures = {key: [] for key, _ in LABELS}
    source = snapshot(folder)
    if record.get("source") != source:
        failures["basic"].append("source bytes changed: restart the three-round audit")
    if record.get("known_defects") != []:
        failures["streak"].append("known defects unresolved")
    streak = clean_rounds(record, source)
    for index in range(1, 4):
        if streak < index:
            failures[f"audit_{index}"].append(f"only {streak} clean consecutive rounds")
    if streak < 3:
        failures["streak"].append("three clean rounds missing")
    readme = folder / "C48" / "README.TXT"
    if not readme.is_file() or len(readme.read_text(errors="replace").strip()) < 50:
        failures["mapping"].append("nonempty C48/README.TXT required as single review note")
    for key, _ in LABELS:
        if key in AUTO:
            continue
        value = record.get("checks", {}).get(key, "NOT_RUN")
        if value == "PASS":
            continue
        if key in CONDITIONAL and isinstance(value, str) and value.startswith("N/A: ") and len(value.strip()) > 12:
            continue
        failures[key].append("not signed off: " + str(value))
    sources = list((folder / "C48").glob("*.c"))
    if len(sources) != 1:
        failures["link"].append("exactly one C48 source required")
    else:
        file = sources[0]
        if not file.with_suffix(".ssx").is_file() or not file.with_suffix(".ssx").read_bytes().startswith(b"SSX1"):
            failures["link"].append("missing or invalid SSX")
        try:
            if tape_stem(file.with_suffix(".tzx").read_bytes()) != file.stem or len(file.stem) > 10:
                failures["tape"].append("internal tape name mismatch")
        except (ValueError, OSError, UnicodeError, IndexError) as exc:
            failures["tape"].append(str(exc))
    failures["repro"].extend(build_twice(folder, sdk))
    tmp = ROOT / "build" / "tmp"
    if not tmp.is_dir() or sorted(p.name for p in tmp.iterdir()) != [".gitkeep"]:
        failures["hygiene"].append("build/tmp is not clean")
    if any(not p.name.endswith("-glyphs.asm") for p in (folder / "C48").glob("*.asm")):
        failures["hygiene"].append("generated assembly found in program source")
    failures["hygiene"].extend(git_errors(folder, False))
    if closeout:
        failures["remote"].extend(git_errors(folder, True))
    blocked = 0
    print("PORT CHECKLIST:", folder.name)
    for index, (key, description) in enumerate(LABELS, 1):
        if key == "remote" and not closeout:
            result = "PENDING"
        elif failures[key]:
            result = "BLOCKED"
            blocked += 1
        else:
            result = "PASS"
        print(f"{index:02d}/21 {result}: {description}")
        for note in failures[key]:
            print("    -", note)
    print("BLOCKED" if blocked else "CLOSEOUT COMPLETE" if closeout else "PREPUSH READY")
    return not blocked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", help="NN-name")
    parser.add_argument("--sdk", type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--init", action="store_true")
    modes.add_argument("--restart", action="store_true")
    modes.add_argument("--closeout", action="store_true")
    args = parser.parse_args()
    folder = ROOT / args.program
    path = folder / "C48" / "PORT-CHECK.json"
    if not re.fullmatch(r"\d\d-[a-z0-9-]+", args.program) or not (folder / "C48").is_dir():
        parser.error("valid numbered C48 directory required")
    if args.init or args.restart:
        if args.init and path.exists():
            parser.error("checklist already exists: use --restart for new source")
        if args.restart and not path.exists():
            parser.error("no checklist to restart: use --init")
        record = {"version": 2, "program": args.program, "source": snapshot(folder),
                  "known_defects": ["NOT REVIEWED"], "audits": [],
                  "checks": {key: "NOT_RUN" for key, _ in LABELS if key not in AUTO}}
        path.write_text(json.dumps(record, indent=2) + "\n")
        print("Initialized:", path)
        return 0
    try:
        record = json.loads(path.read_text())
        if record.get("version") != 2 or record.get("program") != args.program:
            raise ValueError("wrong checklist version or program")
        return 0 if check(folder, record, args.sdk, args.closeout) else 1
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("BLOCKED:", exc)
        for index, (_, name) in enumerate(LABELS, 1):
            print(f"{index:02d}/21 BLOCKED: {name}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

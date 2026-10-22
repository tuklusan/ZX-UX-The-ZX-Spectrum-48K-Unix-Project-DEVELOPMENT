#!/usr/bin/env python3
"""Mandatory per-program completion gate. Fails if any check is missing."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
LABELS = (
    ("basic", "Original BASIC files and bytes"),
    ("mapping", "BASIC-to-C48 mapping"),
    ("references", "Genuine BASIC reference states"),
    ("sdk", "Frozen SDK interfaces"),
    ("data", "Program data and glyph fidelity"),
    ("inputs", "Input and terminal behavior"),
    ("link", "C48 compile and SSX linkage"),
    ("tape", "TZX packaging and internal name"),
    ("runtime", "Actual ZX-UX runtime"),
    ("comparison", "BASIC/C48 result and screen comparison"),
    ("remnants", "No unexplained leftover pixels or objects"),
    ("negative", "Negative tests and regressions"),
    ("audit_1", "Fresh-byte scan and two reviews, round 1"),
    ("audit_2", "Fresh-byte scan and two reviews, round 2"),
    ("audit_3", "Fresh-byte scan and two reviews, round 3"),
    ("streak", "Three successive clean rounds"),
    ("repro", "Two real byte-identical builds"),
    ("yolo", "yolo loading where claimed"),
    ("hygiene", "No generated or forbidden changes"),
    ("checker", "Private checker result"),
    ("remote", "Remote commit and files read back"),
)
AUTO = {"link", "tape", "audit_1", "audit_2", "audit_3", "streak", "repro", "hygiene", "remote"}
OPTIONAL = {"inputs", "remnants", "yolo", "checker"}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def files_snapshot(folder):
    files = [p for p in (folder / "BASIC").rglob("*") if p.is_file()]
    for place in (folder / "C48", ROOT / "c48lib"):
        files.extend(p for p in place.rglob("*") if p.is_file() and p.suffix in (".c", ".h", ".asm", ".py"))
    files.extend(ROOT / "build" / n for n in ("build-c48.py", "check-c48.py", "test-c48.py"))
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(set(files)) if p.is_file()}

def proof(entry):
    if not isinstance(entry, dict) or not entry.get("note", "").strip():
        return ["missing review note"]
    paths = entry.get("proof")
    if not isinstance(paths, list) or not paths:
        return ["no proof files"]
    errors = []
    for name in paths:
        if not isinstance(name, str):
            errors.append("invalid proof reference")
            continue
        file = (ROOT / name).resolve()
        if not file.is_relative_to(ROOT.resolve()) or not file.is_file() or not file.stat().st_size:
            errors.append("unreadable or empty proof: " + name)
    return errors

def audit_streak(record, snapshot):
    clean = 0
    last = None
    rounds = record.get("audits", [])
    if not isinstance(rounds, list):
        return 0
    for index, item in enumerate(rounds, 1):
        errors = []
        if not isinstance(item, dict) or item.get("round") != index:
            clean = 0
            continue
        try:
            time = dt.datetime.fromisoformat(item["time"])
            if time.tzinfo is None or (last is not None and time <= last):
                errors.append("time")
            last = time
        except (ValueError, KeyError, TypeError):
            errors.append("time")
        if item.get("source_sha256") != snapshot or item.get("defects") != []:
            errors.append("stale/defective scan")
        for kind in ("scan", "normal", "adversarial"):
            row = item.get(kind)
            if not isinstance(row, dict) or row.get("status") != "PASS" or not row.get("reviewer"):
                errors.append(kind)
            else:
                errors.extend(proof(row))
        clean = 0 if errors else clean + 1
    return clean

def tape_name(data):
    if not data.startswith(b"ZXTape!\x1a"):
        raise ValueError("not TZX")
    pos = 10
    if data[pos] == 0x30:
        pos += 2 + data[pos + 1]
    if len(data) < pos + 5 or data[pos] != 0x10:
        raise ValueError("TZX header missing")
    size = int.from_bytes(data[pos + 3:pos + 5], "little")
    block = data[pos + 5:pos + 5 + size]
    if len(block) != size or len(block) < 13 or block[:2] != b"\0\x04":
        raise ValueError("not an executable header")
    return block[2:12].decode("ascii").rstrip()

def run(args, cwd, timeout=90):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)

def git_scope(folder, closeout):
    try:
        root = Path(run(["git", "rev-parse", "--show-toplevel"], folder).stdout.strip()).resolve()
        if root / "src/bonus/60-programs" != ROOT.resolve():
            return ["wrong Git checkout"]
        changes = run(["git", "status", "--porcelain", "--untracked-files=all"], root)
        if changes.returncode:
            return ["Git status failed"]
        errors = []
        for line in changes.stdout.splitlines():
            for name in line[3:].split(" -> "):
                name = name.strip('"')
                if not name.startswith("src/bonus/60-programs/") or "/BASIC/" in name:
                    errors.append("unapproved working-tree change: " + name)
        if closeout:
            if changes.stdout.strip():
                errors.append("local checkout has uncommitted files at final delivery")
            local = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
            live = run(["git", "ls-remote", "origin", "refs/heads/main"], root, 30)
            if live.returncode or not live.stdout.strip():
                return errors + ["live remote read-back failed"]
            remote = live.stdout.split()[0]
            if local != remote:
                errors.append("HEAD does not equal live remote main")
            diff = run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", local], root)
            if diff.returncode or not diff.stdout.strip():
                errors.append("cannot read pushed changed-path list")
            else:
                for path in diff.stdout.splitlines():
                    if not path.startswith("src/bonus/60-programs/") or "/BASIC/" in path:
                        errors.append("forbidden changed path in commit: " + path)
            for p in [folder / "C48" / "PORT-CHECK.json", *(folder / "C48").glob("*.c"),
                      *(folder / "C48").glob("*.ssx"), *(folder / "C48").glob("*.tzx")]:
                relative = p.relative_to(root).as_posix()
                if run(["git", "ls-files", "--error-unmatch", relative], root).returncode:
                    errors.append("file missing from remote commit: " + relative)
                elif run(["git", "diff", "--quiet", "HEAD", "--", relative], root).returncode:
                    errors.append("local file differs from committed bytes: " + relative)
        return errors
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return ["Git scope/remote checks unavailable"]

def rebuild(folder, sdk):
    src = list((folder / "C48").glob("*.c"))
    if len(src) != 1:
        return ["exactly one C48 source required"]
    outputs = [src[0].with_suffix(x) for x in (".ssx", ".tzx")]
    baseline = {p.name: digest(p) for p in outputs if p.is_file()}
    args = [sys.executable, str(ROOT / "build" / "build-c48.py")]
    if sdk:
        args += ["--sdk", str(sdk)]
    args += [folder.name]
    snapshots = []
    for turn in (1, 2):
        try:
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            r = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
        except (OSError, subprocess.TimeoutExpired):
            return ["build invocation failed or timed out"]
        if r.returncode or any(not p.is_file() for p in outputs):
            return [f"build {turn} failed: " + (r.stderr or r.stdout)[-300:]]
        snapshots.append({p.name: digest(p) for p in outputs})
    if not baseline or snapshots[0] != snapshots[1] or baseline != snapshots[0]:
        return ["two builds differ from each other or from submitted files"]
    return []

def validate(folder, record, closeout, sdk):
    errors = {key: [] for key, _ in LABELS}
    current = files_snapshot(folder)
    if record.get("source_sha256") != current:
        errors["basic"].append("source bytes changed; restart all audits")
    if record.get("known_defects") != []:
        errors["streak"].append("known defects not cleared")
    streak = audit_streak(record, current)
    for n in (1, 2, 3):
        if streak < n:
            errors["audit_" + str(n)].append(f"only {streak} consecutive clean rounds")
    if streak < 3:
        errors["streak"].append("three clean rounds missing")
    checks = record.get("checks", {})
    for key, _ in LABELS:
        if key in AUTO:
            continue
        entry = checks.get(key, {}) if isinstance(checks, dict) else {}
        status = entry.get("status") if isinstance(entry, dict) else None
        if status == "NOT_APPLICABLE" and key in OPTIONAL:
            errors[key].extend(proof(entry))
        elif status != "PASS":
            errors[key].append("unverified: " + str(status))
        else:
            errors[key].extend(proof(entry))
    sources = list((folder / "C48").glob("*.c"))
    if len(sources) != 1:
        errors["link"].append("C48 source missing or ambiguous")
    else:
        stem = sources[0].stem
        ssx, tzx = (sources[0].with_suffix(x) for x in (".ssx", ".tzx"))
        if not ssx.is_file() or not ssx.read_bytes().startswith(b"SSX1"):
            errors["link"].append("invalid SSX")
        if not tzx.is_file():
            errors["tape"].append("TZX missing")
        else:
            try:
                if tape_name(tzx.read_bytes()) != stem or len(stem) > 10:
                    errors["tape"].append("wrong internal TZX name")
            except (ValueError, UnicodeError, IndexError) as ex:
                errors["tape"].append(str(ex))
        hashes = {p.name: digest(p) for p in (ssx, tzx) if p.is_file()}
        if hashes != record.get("binary_sha256"):
            errors["repro"].append("binary SHA-256 differs from reviewed outputs")
    errors["repro"].extend(rebuild(folder, sdk))
    rb = record.get("rebuild", {})
    if not isinstance(rb, dict) or rb.get("status") != "PASS" or rb.get("first") != rb.get("second") or rb.get("first") != record.get("binary_sha256"):
        errors["repro"].append("two earlier matching build records missing")
    else:
        errors["repro"].extend(proof(rb))
    tmp = ROOT / "build" / "tmp"
    if not tmp.is_dir() or sorted(p.name for p in tmp.iterdir()) != [".gitkeep"]:
        errors["hygiene"].append("temporary directory not clean")
    if [p for p in (folder / "C48").glob("*.asm") if not p.name.endswith("-glyphs.asm")]:
        errors["hygiene"].append("generated assembler companion in source directory")
    errors["hygiene"].extend(git_scope(folder, False))
    if closeout:
        errors["remote"].extend(git_scope(folder, True))
    print(f"PORT CHECKLIST: {folder.name}")
    failures = 0
    for i, (key, title) in enumerate(LABELS, 1):
        if key == "remote" and not closeout:
            flag = "PENDING"
        elif errors[key]:
            failures += 1
            flag = "BLOCKED"
        else:
            flag = "PASS"
        print(f"{i:02d}/21 {flag}: {title}")
        for error in errors[key]:
            print("     - " + error)
    print("CLOSEOUT COMPLETE" if not failures and closeout else
          "PREPUSH READY" if not failures else f"BLOCKED: {failures} items")
    return not failures

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program")
    parser.add_argument("--sdk", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--init", action="store_true")
    mode.add_argument("--restart", action="store_true")
    mode.add_argument("--closeout", action="store_true")
    args = parser.parse_args()
    folder = ROOT / args.program
    path = folder / "C48" / "PORT-CHECK.json"
    if not re.fullmatch(r"\d\d-[a-z0-9-]+", args.program) or not (folder / "C48").is_dir():
        parser.error("numbered C48 program directory required")
    if args.init or args.restart:
        if args.init and path.exists():
            parser.error("checklist exists: use --restart after corrections")
        if args.restart and not path.exists():
            parser.error("no checklist: use --init")
        old = json.loads(path.read_text()) if args.restart else {}
        history = old.get("history", []) + ([{"source_sha256": old.get("source_sha256"),
                 "audits": old.get("audits"), "known_defects": old.get("known_defects")}] if old else [])
        doc = {"version": 1, "program": args.program, "source_sha256": files_snapshot(folder),
               "known_defects": ["NOT REVIEWED"], "audits": [], "history": history,
               "checks": {key: {"status": "NOT_RUN", "note": "", "proof": []}
                          for key, _ in LABELS if key not in AUTO},
               "binary_sha256": {}, "rebuild": {"status": "NOT_RUN"}}
        path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print("Created unverified checklist: " + str(path))
        return 0
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("version") != 1 or doc.get("program") != args.program:
            raise ValueError("wrong checklist version or program")
        return 0 if validate(folder, doc, args.closeout, args.sdk) else 1
    except (OSError, ValueError, KeyError, TypeError) as ex:
        print("BLOCKED: " + str(ex))
        for i, (_, label) in enumerate(LABELS, 1):
            print(f"{i:02d}/21 BLOCKED: {label}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Read or advance the committed 60-program porting cursor.

The progress file lives in GitHub main and is updated in the SAME commit as
its newly completed C48 port. No progress is claimed for uncommitted work.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
PROGRESS = "PORTING-PROGRESS.json"
NAME = re.compile(r"(?:0[1-9]|[1-5][0-9]|60)-[a-z0-9-]+\Z")
CHECKS = ("normal", "adversarial", "integration", "remnants")


class ProgressError(ValueError):
    pass


def programs(root=ROOT):
    result = sorted(p.name for p in root.iterdir() if p.is_dir() and NAME.fullmatch(p.name))
    if len(result) != 60 or [int(p[:2]) for p in result] != list(range(1, 61)):
        raise ProgressError("expected exactly 60 consecutive numbered program directories")
    return result


def load_progress(root=ROOT):
    try:
        data = json.loads((root / PROGRESS).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProgressError("cannot read progress file: " + str(exc)) from exc
    names = programs(root)
    if not isinstance(data, dict) or set(data) != {"schema", "completed", "next_program"}:
        raise ProgressError("unknown progress file fields")
    if type(data["schema"]) is not int or data["schema"] != 1:
        raise ProgressError("unsupported progress schema")
    done = data["completed"]
    if not isinstance(done, list) or done != names[:len(done)]:
        raise ProgressError("completed programs must be a consecutive prefix in 01-60 order")
    if data["next_program"] != (names[len(done)] if len(done) < 60 else None):
        raise ProgressError("next_program does not match first incomplete program")
    return data


def checked_result(root, program):
    folder = root / program / "C48"
    report = folder / "PORT-RESULT.txt"
    sources = list(folder.glob("*.c"))
    if len(sources) != 1:
        raise ProgressError(program + ": expected exactly one C48 source")
    stem = sources[0].stem
    if not (folder / (stem + ".ssx")).is_file() or not (folder / (stem + ".tzx")).is_file():
        raise ProgressError(program + ": SSX/TZX not present")
    try:
        lines = report.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ProgressError(program + ": PORT-RESULT.txt missing") from exc
    expected = {"Program: " + program, "Build: PASS", "TZX: PASS",
                "Git scope: PASS", "Delivery: PENDING"}
    if not expected.issubset(set(lines)):
        raise ProgressError(program + ": release gate has not returned READY")
    for key in CHECKS:
        ok = "CHECK " + key + " PASS" in lines
        if key == "remnants":
            ok = ok or "CHECK remnants NA" in lines
        if not ok:
            raise ProgressError(program + ": missing passed " + key + " check")


def complete(root, program):
    data = load_progress(root)
    if program != data["next_program"]:
        raise ProgressError("out of order: next program is " + str(data["next_program"]))
    checked_result(root, program)
    next_done = data["completed"] + [program]
    names = programs(root)
    updated = {"schema": 1, "completed": next_done,
               "next_program": names[len(next_done)] if len(next_done) < len(names) else None}
    (root / PROGRESS).write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
    return updated


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=("status", "complete"))
    cli.add_argument("program", nargs="?")
    args = cli.parse_args()
    try:
        if args.command == "complete":
            if not args.program:
                cli.error("complete requires NN-name")
            data = complete(ROOT, args.program)
        else:
            if args.program:
                cli.error("status does not take a program")
            data = load_progress(ROOT)
        print("Completed: {}/60".format(len(data["completed"])))
        print("Last completed: " + (data["completed"][-1] if data["completed"] else "none"))
        print("Next program: " + (data["next_program"] or "ALL DONE"))
        return 0
    except ProgressError as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

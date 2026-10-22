#!/usr/bin/env python3
"""Single-build C48 release checks; no manual checklists or repeat builds.

From src/bonus/60-programs:
  python build/check-c48.py NN-name --system ZX-UX.tzx --sdk SDK
  python build/check-c48.py NN-name --system ZX-UX.tzx --sdk SDK --closeout

Program tests print CHECK normal/adversarial/integration/remnants PASS after
real assertions. At closeout, validate the published Git commit, not a new build.
"""
from __future__ import annotations
import argparse
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TMP = ROOT / "build" / "tmp"
PREFIX = "src/bonus/60-programs/"
REQUIRED = ("normal", "adversarial", "integration", "remnants")


def execute(argv, cwd=ROOT, timeout=240):
    try:
        return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                              timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None


def git_scope(program, closeout):
    r = execute(["git", "rev-parse", "--show-toplevel"])
    if r is None or r.returncode:
        return ["Git checkout not available"], None
    base = pathlib.Path(r.stdout.strip()).resolve()
    if (base / PREFIX).resolve() != ROOT.resolve():
        return ["not in the expected repository checkout"], base
    errors = []
    result = execute(["git", "status", "--porcelain", "--untracked-files=all", "-z"], base)
    if result is None or result.returncode:
        return ["cannot read Git worktree status"], base
    records = result.stdout.split("\0")
    index = 0
    while index < len(records) and records[index]:
        record = records[index]
        kind = record[:2]
        candidates = [record[3:]]
        if "R" in kind or "C" in kind:
            index += 1
            if index >= len(records) or not records[index]:
                errors.append("malformed Git rename record")
                break
            candidates.append(records[index])
        for name in candidates:
            if not name.startswith(PREFIX) or "/BASIC/" in name:
                errors.append("unauthorized Git path: " + name)
        index += 1
    if closeout:
        if result.stdout.strip("\0"):
            errors.append("uncommitted files at closeout")
        paths = execute(["git", "diff-tree", "--no-commit-id", "--name-only",
                         "-r", "HEAD"], base)
        if paths is None or paths.returncode or not paths.stdout.strip():
            errors.append("cannot inspect last commit changes")
        else:
            for name in paths.stdout.splitlines():
                if not name.startswith(PREFIX) or "/BASIC/" in name:
                    errors.append("unauthorized committed path: " + name)
    return errors, base


def tape_stem(blob):
    if not blob.startswith(b"ZXTape!\x1a") or len(blob) < 15:
        raise ValueError("invalid TZX header")
    i = 10
    if blob[i] == 0x30:
        i += 2 + blob[i + 1]
    if i + 5 > len(blob) or blob[i] != 0x10:
        raise ValueError("missing tape data header")
    size = int.from_bytes(blob[i + 3:i + 5], "little")
    data = blob[i + 5:i + 5 + size]
    if len(data) != size or len(data) < 13 or data[:2] != b"\0\x04":
        raise ValueError("invalid executable tape header")
    return data[2:12].decode("ascii").rstrip()


def basic_files_ok(program):
    folder = ROOT / program / "BASIC"
    return folder.is_dir() and bool(list(folder.glob("*.bas")))


def port_files(program):
    folder = ROOT / program / "C48"
    sources = list(folder.glob("*.c"))
    if len(sources) != 1:
        raise ValueError("expected exactly one C48 .c source")
    src = sources[0]
    if len(src.stem) > 10:
        raise ValueError("tape name exceeds 10 characters")
    return folder, src, src.with_suffix(".ssx"), src.with_suffix(".tzx")


def binary_errors(ssx, tzx, stem):
    problems = []
    try:
        if not ssx.read_bytes().startswith(b"SSX1"):
            problems.append("invalid SSX")
    except OSError:
        problems.append("SSX not found")
    try:
        if tape_stem(tzx.read_bytes()) != stem:
            problems.append("TZX internal name mismatch")
    except (OSError, ValueError, UnicodeError, IndexError) as exc:
        problems.append("TZX missing or invalid: " + str(exc))
    return problems


def test_result(stdout):
    verdict = {}
    for line in stdout.splitlines():
        m = re.fullmatch(r"CHECK (normal|adversarial|integration|remnants) (PASS|NA)", line.strip())
        if m:
            if m[1] in verdict:
                return None, "duplicate CHECK marker: " + m[1]
            verdict[m[1]] = m[2]
    for item in REQUIRED:
        if item not in verdict:
            return None, "missing CHECK marker: " + item
        if verdict[item] == "NA" and item != "remnants":
            return None, "invalid NA: " + item
    return verdict, None


def clean_tmp():
    if not TMP.is_dir():
        return ["build/tmp missing"]
    for path in TMP.iterdir():
        if path.name == ".gitkeep":
            continue
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()
    return [] if (TMP / ".gitkeep").is_file() else ["build/tmp/.gitkeep missing"]


def remote_errors(repo, folder):
    errors = []
    local = execute(["git", "rev-parse", "HEAD"], repo)
    remote = execute(["git", "ls-remote", "origin", "refs/heads/main"], repo, 30)
    if (local is None or local.returncode or remote is None or remote.returncode
            or not remote.stdout.strip()):
        return ["live remote GitHub verification unavailable"]
    head = local.stdout.strip()
    if head != remote.stdout.split()[0]:
        errors.append("HEAD differs from remote main")
    for file in sorted(folder.rglob("*")):
        if not file.is_file() or file.name.startswith("."):
            continue
        path = file.relative_to(repo).as_posix()
        tracked = execute(["git", "ls-files", "--error-unmatch", "--", path], repo)
        diff = execute(["git", "diff", "--quiet", "HEAD", "--", path], repo)
        if tracked is None or tracked.returncode:
            errors.append("not committed: " + path)
        elif diff is None or diff.returncode:
            errors.append("differs from committed version: " + path)
    return errors


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("program")
    cli.add_argument("--system", required=True, type=pathlib.Path)
    cli.add_argument("--sdk", required=True, type=pathlib.Path)
    cli.add_argument("--test", type=pathlib.Path)
    cli.add_argument("--closeout", action="store_true")
    args = cli.parse_args()
    sys.dont_write_bytecode = True
    errors = []
    if not re.fullmatch(r"\d\d-[a-z0-9-]+", args.program):
        cli.error("expected a numbered program directory")
    program = ROOT / args.program
    try:
        folder, source, ssx, tzx = port_files(args.program)
    except ValueError as exc:
        print("BLOCKED:", exc)
        return 1
    if not basic_files_ok(args.program):
        errors.append("original BASIC listing not found")
    if not args.system.is_file() or not args.sdk.is_dir():
        errors.append("system tape or SDK unavailable")
    scope, repo = git_scope(args.program, args.closeout)
    errors += scope
    if args.closeout:
        errors += binary_errors(ssx, tzx, source.stem)
        if not (folder / "PORT-RESULT.txt").is_file():
            errors.append("automatically generated PORT-RESULT.txt missing")
        else:
            report = (folder / "PORT-RESULT.txt").read_text()
            checks, issue = test_result(report)
            if issue:
                errors.append("incomplete test result: " + issue)
        if repo is not None:
            errors += remote_errors(repo, folder)
        print("CLOSEOUT COMPLETE" if not errors else "BLOCKED")
        for item in errors:
            print("FAIL:", item)
        return bool(errors)

    if not errors:
        build = execute([sys.executable, str(ROOT / "build" / "build-c48.py"),
                         "--sdk", str(args.sdk.resolve()), args.program], timeout=240)
        if build is None or build.returncode:
            errors.append("single frozen build failed or timed out")
            if build:
                print(build.stderr[-1500:])
    if not errors:
        errors += binary_errors(ssx, tzx, source.stem)
    if not errors:
        test = args.test or folder / ("test-" + source.stem + ".py")
        test = (ROOT / test).resolve() if not test.is_absolute() else test.resolve()
        if not test.is_file() or not test.is_relative_to(ROOT):
            errors.append("missing program-specific test inside the permitted workspace")
        else:
            result = execute([sys.executable, str(test), "--system", str(args.system.resolve()),
                              "--sdk", str(args.sdk.resolve())], timeout=300)
            if result is None or result.returncode:
                errors.append("program tests failed or timed out")
                if result:
                    print((result.stdout + result.stderr)[-2000:])
            else:
                verdict, problem = test_result(result.stdout)
                if problem:
                    errors.append(problem)
    if not errors:
        errors += clean_tmp()
    if not errors:
        lines = ["Program: " + args.program,
                 "System: " + args.system.name,
                 "Build: PASS", "TZX: PASS",
                 *["CHECK " + k + " " + verdict[k] for k in REQUIRED],
                 "Git scope: PASS", "Delivery: PENDING"]
        (folder / "PORT-RESULT.txt").write_text("\n".join(lines) + "\n")
    print("READY" if not errors else "BLOCKED")
    for problem in errors:
        print("FAIL:", problem)
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())

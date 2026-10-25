"""Recompute actual published RBC SSX sizes through pinned upeepz80 output stage.

Results are written only to untracked build/tmp, never to source/bin trees.
Exactly the existing linked images are compared byte-for-byte. No alternate
or patched executable may be counted as a success.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from upeepz80_output import UPSTREAM_REVISION, optimize_ssx


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def measure(root, workspace):
    import ras
    import rld

    games = sorted((root / "src/bonus/60-programs").glob("[0-9][0-9]-*"))
    if len(games) != 60:
        raise ValueError("expected 60 original game folders")
    binaries = []
    for game in games:
        binpath = game / "bin"
        files = sorted(p for p in binpath.iterdir() if p.is_file())
        if len(files) != 1:
            raise ValueError(f"{game.name}: expected exactly one outcome")
        f = files[0]
        if f.name == game.name + ".ssx":
            binaries.append(f)
        elif f.name != "README.md":
            raise ValueError(f"{game.name}: non-SSX outcome is not README")
    if not binaries:
        raise ValueError("no actually linked SSX outputs to optimize")

    rows = []
    for file in binaries:
        before = file.read_bytes()
        after, meta = optimize_ssx(before, rld, ras)
        if before != after:
            raise AssertionError(file.name + ": nonidentical output from optimizer")
        row = {
            "game": file.parent.parent.name,
            "source": str(file.relative_to(root)),
            "baseline_sha256": sha256(before),
            "optimized_sha256": sha256(after),
            **meta,
        }
        rows.append(row)
        print(f"{row['game']}: linked {len(before)} -> {len(after)} bytes, "
              f"image {meta['input_image_bytes']} -> {meta['linked_image_bytes']}, "
              f"memory {meta['input_memory_required']} -> {meta['linked_memory_required']}",
              flush=True)
    report = {
        "upstream_repo": "https://github.com/tuklusan/upeepz80",
        "upstream_revision": UPSTREAM_REVISION,
        "recompute_mode": "native-SSX-to-db-dw-assembly-to-upeepz80-to-ras-to-rld",
        "outputs": len(rows),
        "total_disk_before": sum(x["input_file_bytes"] for x in rows),
        "total_disk_after": sum(x["linked_file_bytes"] for x in rows),
        "total_memory_before": sum(x["input_memory_required"] for x in rows),
        "total_memory_after": sum(x["linked_memory_required"] for x in rows),
        "total_saved_disk": sum(x["saved_file_bytes"] for x in rows),
        "total_saved_memory": sum(x["saved_memory_bytes"] for x in rows),
        "rows": rows,
    }
    workspace.mkdir(parents=True,exist_ok=True)
    (workspace / "upeepz80-ssx-sizes.json").write_text(
        json.dumps(report,sort_keys=True,indent=2) + "\n"
    )
    if len(rows) != len(binaries):
        raise AssertionError("incomplete measurements")
    print("SUMMARY",json.dumps({k:v for k,v in report.items() if k not in ("rows",)},
                               sort_keys=True), flush=True)
    return report


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path.cwd())
    parser.add_argument("--workspace",type=Path,default=Path("build/tmp/upeepz80-ssx"))
    a=parser.parse_args()
    measure(a.root.resolve(), a.workspace.resolve())

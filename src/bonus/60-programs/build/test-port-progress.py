#!/usr/bin/env python3
"""Focused regression tests for the durable program cursor, without a build."""
import importlib.util
import json
import pathlib
import tempfile
import unittest

THIS = pathlib.Path(__file__).resolve().parent / "port_progress.py"
spec = importlib.util.spec_from_file_location("progress", THIS)
progress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(progress)


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.names = [f"{i:02d}-example{i}" for i in range(1, 61)]
        for p in self.names:
            (self.root / p).mkdir()
        self.write(0)

    def write(self, count, next_override="UNSET", pilots=()):
        names = [n for n in self.names if n not in pilots]
        obj = {"schema": 2, "completed": names[:count],
               "pilot_completed": list(pilots),
               "next_program": names[count] if count < len(names) else None}
        if next_override != "UNSET":
            obj["next_program"] = next_override
        (self.root / progress.PROGRESS).write_text(json.dumps(obj) + "\n")

    def create_valid_port(self, name):
        d = self.root / name / "C48"
        d.mkdir()
        (d / "sample.c").write_text("int main(void){return 0;}\n")
        (d / "sample.ssx").write_bytes(b"SSX1")
        (d / "sample.tzx").write_bytes(b"ZXTape!\x1a")
        lines = ["Program: " + name, "Build: PASS", "TZX: PASS", "Git scope: PASS",
                 "Delivery: PENDING"] + ["CHECK " + x + " PASS" for x in progress.CHECKS]
        (d / "PORT-RESULT.txt").write_text("\n".join(lines) + "\n")

    def test_initial_cursor(self):
        self.write(1)
        state = progress.load_progress(self.root)
        self.assertEqual(state["next_program"], self.names[1])

    def test_invalid_gap_rejected(self):
        obj = {"schema": 2, "completed": [self.names[1]], "pilot_completed": [], "next_program": self.names[2]}
        (self.root / progress.PROGRESS).write_text(json.dumps(obj))
        with self.assertRaises(progress.ProgressError):
            progress.load_progress(self.root)

    def test_stale_cursor_rejected(self):
        self.write(1, next_override=self.names[0])
        with self.assertRaises(progress.ProgressError):
            progress.load_progress(self.root)

    def test_cannot_mark_unverified_port(self):
        self.write(1)
        with self.assertRaises(progress.ProgressError):
            progress.complete(self.root, self.names[1])
        self.assertEqual(progress.load_progress(self.root)["next_program"], self.names[1])

    def test_out_of_order_rejected(self):
        self.write(1)
        self.create_valid_port(self.names[2])
        with self.assertRaises(progress.ProgressError):
            progress.complete(self.root, self.names[2])

    def test_ready_port_advances_once(self):
        self.write(1)
        self.create_valid_port(self.names[1])
        state = progress.complete(self.root, self.names[1])
        self.assertEqual(state["completed"], self.names[:2])
        self.assertEqual(state["next_program"], self.names[2])
        with self.assertRaises(progress.ProgressError):
            progress.complete(self.root, self.names[1])

    def test_last_program_sets_all_done(self):
        self.write(59)
        self.create_valid_port(self.names[-1])
        self.assertIsNone(progress.complete(self.root, self.names[-1])["next_program"])

    def test_pilot_exemptions_do_not_move_cursor(self):
        self.names[24] = "25-galaxians"
        self.names[57] = "58-invaders"
        for name in ("25-galaxians", "58-invaders"):
            (self.root / name).mkdir()
            (self.root / ("25-example25" if name.startswith("25") else "58-example58")).rmdir()
        self.write(1, pilots=("25-galaxians", "58-invaders"))
        state = progress.load_progress(self.root)
        self.assertEqual(state["next_program"], self.names[1])
        self.assertEqual(len(state["pilot_completed"]) + len(state["completed"]), 3)

    def test_sequence_skips_pilots_when_reached(self):
        self.names[24] = "25-galaxians"
        self.names[57] = "58-invaders"
        for name, former in (("25-galaxians", "25-example25"), ("58-invaders", "58-example58")):
            (self.root / former).rename(self.root / name)
        pilots = ("25-galaxians", "58-invaders")
        self.write(24, pilots=pilots)
        self.assertEqual(progress.load_progress(self.root)["next_program"], self.names[25])
        self.create_valid_port(self.names[25])
        self.assertEqual(progress.complete(self.root, self.names[25])["next_program"], self.names[26])
        self.write(55, pilots=pilots)
        self.assertEqual(progress.load_progress(self.root)["next_program"], self.names[56])
        self.create_valid_port(self.names[56])
        self.assertEqual(progress.complete(self.root, self.names[56])["next_program"], self.names[58])

    def test_nonpilot_gap_and_unknown_pilot_rejected(self):
        self.write(1, pilots=("25-galaxians", "58-invaders"))
        with self.assertRaises(progress.ProgressError):
            progress.load_progress(self.root)
        self.write(1, pilots=(self.names[2],))
        with self.assertRaises(progress.ProgressError):
            progress.load_progress(self.root)

    def test_checker_marker_required(self):
        self.write(0)
        self.create_valid_port(self.names[0])
        report = self.root / self.names[0] / "C48" / "PORT-RESULT.txt"
        report.write_text(report.read_text().replace("CHECK integration PASS", "CHECK integration FAILED"))
        with self.assertRaises(progress.ProgressError):
            progress.complete(self.root, self.names[0])


if __name__ == "__main__":
    unittest.main()

"""Additional regression checks for the v1.2.0 public release."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "rename_greek_to_greeklish.py"
spec = importlib.util.spec_from_file_location("renamer_extra", SCRIPT)
ren = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ren)


class ReleaseRegressionTests(unittest.TestCase):
    def test_no_greek_does_not_plan_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "English Song.mp3").write_bytes(b"unchanged")
            (base / "Dimitris Laidis.pdf").write_bytes(b"unchanged")
            self.assertEqual(ren.plan_renames(base, recursive=True), [])

    def test_only_greek_part_of_mixed_name_changes(self):
        self.assertEqual(ren.to_greeklish("DJ - Ελληνικά"), "DJ - Ellinika")

    def test_extensions_and_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "Μουσική.FLAC").write_bytes(b"\x00test\xff")
            plan = ren.plan_renames(base)
            self.assertEqual(plan[0][1].name, "Mousiki.FLAC")
            renamed, logfile = ren.apply_plan(base, plan)
            self.assertEqual(renamed, 1)
            self.assertEqual((base / "Mousiki.FLAC").read_bytes(), b"\x00test\xff")
            self.assertTrue(logfile.is_file())

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(ren.plan_renames(Path(directory), recursive=True), [])

    def test_nested_folder_requires_recursive_yes(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            nested = base / "Ελληνικά"
            nested.mkdir()
            (nested / "Τραγούδι.mp3").write_bytes(b"sample")
            self.assertEqual(ren.plan_renames(base, recursive=False), [])
            self.assertEqual(len(ren.plan_renames(base, recursive=True)), 2)

    def test_default_folder_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("builtins.input", return_value=""):
                self.assertEqual(ren.choose_folder(Path(directory)), Path(directory).resolve())

    def test_undo_guard_invalid_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            log = base / "bad.csv"
            log.write_text("wrong,columns\nfoo,bar\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                ren.undo(base, log, confirmed=True)

    def test_dry_run_does_not_touch_anything(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path = base / "Ελληνικά.mp3"
            path.write_bytes(b"still-here")
            rc = ren.main(["--path", str(base), "--no-recursive", "--dry-run"])
            self.assertEqual(rc, 0)
            self.assertEqual(path.read_bytes(), b"still-here")
            self.assertEqual(list(base.glob("greeklish_rename_log_*.csv")), [])


if __name__ == "__main__":
    unittest.main()

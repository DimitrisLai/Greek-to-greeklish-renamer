"""History viewer and safe CSV/atomic collision regression tests."""
import csv
import errno
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from csv_safety import spreadsheet_cell
from history_service import list_history, read_history
from rename_greek_to_greeklish import apply_plan, rename_no_overwrite
from renamer_service import create_preview, execute_preview_report, restore_log


class HistoryTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)

    def test_history_detects_runs_and_displays_exact_paths(self):
        greek = self.root / 'Αθήνα.mp3'
        greek.write_bytes(b'audio')
        preview = create_preview(self.root, recursive=False, rename_folders=False)
        report = execute_preview_report(preview, preview.operations)
        self.assertEqual(report.renamed_count, 1)
        found = list_history(self.root)
        self.assertEqual(len(found), 1)
        detail = read_history(self.root, found[0].path)
        self.assertEqual(detail.changes, 1)
        self.assertEqual(detail.preview_rows[0][0], 'Αθήνα.mp3')
        self.assertEqual(detail.preview_rows[0][1], preview.operations[0][1].name)
        self.assertEqual(restore_log(self.root, found[0].path), (1, 1))
        self.assertEqual(greek.read_bytes(), b'audio')
        self.assertEqual(read_history(self.root, found[0].path).changes, 1)

    def test_history_rejects_foreign_and_malicious_logs(self):
        other_dir = self.root / 'other'
        other_dir.mkdir()
        external = other_dir / 'greeklish_rename_log_2026.csv'
        external.write_text('old_relative_path,new_relative_path\nx,y\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            read_history(self.root, external)
        invalid = self.root / 'greeklish_rename_log_invalid.csv'
        invalid.write_text('old_relative_path,new_relative_path\n../outside,x\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            read_history(self.root, invalid)
        invalid.write_text('old_relative_path,new_relative_path\n/a,x\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            read_history(self.root, invalid)

    def test_history_limits_rows_and_count(self):
        logfile = self.root / 'greeklish_rename_log_example.csv'
        with logfile.open('w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(['old_relative_path', 'new_relative_path'])
            for n in range(50):
                w.writerow([f'Αρχείο{n}.txt', f'Archeio{n}.txt'])
        detail = read_history(self.root, logfile, max_preview_rows=10)
        self.assertEqual(detail.changes, 50)
        self.assertEqual(len(detail.preview_rows), 10)
        self.assertTrue(detail.truncated)

    def test_other_files_and_links_not_in_history(self):
        (self.root / 'greeklish_result_log_example.csv').write_text('a,b', encoding='utf-8')
        (self.root / 'other.csv').write_text('a,b', encoding='utf-8')
        self.assertEqual(list_history(self.root), ())


class ExportAndCollisionTests(unittest.TestCase):
    def test_spreadsheet_formula_values_protected(self):
        for value in ('=cmd|foo', '+SUM(1,2)', '-HYPERLINK("x")', '@SUM(1,1)',
                      '  =cmd', '\t=cmd', '\n=cmd'):
            safe = spreadsheet_cell(value)
            self.assertTrue(safe.startswith("'"), repr(safe))
            self.assertEqual(safe[1:], value)
        for name in ('Αθήνα.mp3', 'Song - mix.flac', 'normal.txt'):
            self.assertEqual(spreadsheet_cell(name), name)

    def test_export_report_csv_uses_spreadsheet_safe_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / '=BAD(1).txt'
            bad.write_bytes(b'keep')
            report_file = root / 'test_report.csv'
            from renamer_service import RenameRecord, RenameReport
            record = RenameRecord(bad, root/'@BAD(2).txt', 'failed', '=message')
            report = RenameReport(root, root/'undo.csv', (record,), 1, 1, 0, 0, 1, 0, 0, False)
            report.export_csv(report_file)
            with report_file.open(encoding='utf-8-sig', newline='') as f:
                row = next(csv.DictReader(f))
            for field in ('reason', 'original_relative_path', 'proposed_relative_path'):
                self.assertTrue(row[field].startswith("'"))

    def test_atomic_no_replace_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, new = root/'α.txt', root/'name.txt'
            old.write_bytes(b'old original')
            new.write_bytes(b'occupied destination')
            with self.assertRaises((FileExistsError, OSError)):
                rename_no_overwrite(old, new)
            self.assertEqual(old.read_bytes(), b'old original')
            self.assertEqual(new.read_bytes(), b'occupied destination')

    def test_atomic_no_replace_existing_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, new = root/'ελληνικά', root/'ellinika'
            old.mkdir(); new.mkdir()
            (old/'a.txt').write_bytes(b'from old')
            (new/'b.txt').write_bytes(b'from existing')
            with self.assertRaises((FileExistsError, OSError)):
                rename_no_overwrite(old, new)
            self.assertEqual((old/'a.txt').read_bytes(), b'from old')
            self.assertEqual((new/'b.txt').read_bytes(), b'from existing')

    def test_race_no_overwrite_and_reasons(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root/'Αρχείο.txt'
            target = root/'Archeio.txt'
            old.write_bytes(b'original')
            native = rename_no_overwrite
            def race(source, destination):
                target.write_bytes(b'competitor')
                return native(source, destination)
            rows = []
            with patch('rename_greek_to_greeklish.rename_no_overwrite', side_effect=race):
                with redirect_stdout(io.StringIO()):
                    num, log = apply_plan(root, [(old, target)], result_callback=lambda *args: rows.append(args))
            self.assertEqual(num, 0)
            self.assertEqual(rows[0][2], 'skipped')
            self.assertEqual(target.read_bytes(), b'competitor')
            self.assertEqual(old.read_bytes(), b'original')

    def test_undo_no_overwrite_after_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root/'Αθήνα.mp3'
            old.write_bytes(b'original')
            preview = create_preview(root, recursive=False, rename_folders=False)
            report = execute_preview_report(preview, preview.operations)
            self.assertEqual(report.renamed_count, 1)
            old.write_bytes(b'occupied')
            self.assertEqual(restore_log(root, report.log), (0, 1))
            self.assertEqual(old.read_bytes(), b'occupied')
            self.assertTrue(preview.operations[0][1].exists())

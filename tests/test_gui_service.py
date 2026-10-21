"""Regression tests for the Windows UI's headless service adapter."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from renamer_service import (PreviewChangedError, create_preview, execute_preview,
                             restore_log)


class GUIServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)

    def touch(self, path: str, contents=b'unchanged'):
        file = self.folder / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(contents)
        return file

    def test_greek_only_and_file_contents(self):
        self.touch('Αθήνα.mp3', b'music')
        self.touch('English.mp3', b'english')
        preview = create_preview(self.folder, recursive=False, rename_folders=False)
        self.assertEqual(preview.count, 1)
        renamed, log = execute_preview(preview)
        self.assertEqual(renamed, 1)
        self.assertEqual((self.folder / 'Athina.mp3').read_bytes(), b'music')
        self.assertEqual((self.folder / 'English.mp3').read_bytes(), b'english')
        self.assertEqual(restore_log(self.folder, log), (1, 1))
        self.assertTrue((self.folder / 'Αθήνα.mp3').is_file())

    def test_recursive_with_folder_names_off(self):
        self.touch('Ελληνικά/Μουσική.mp3')
        preview = create_preview(self.folder, recursive=True, rename_folders=False)
        self.assertEqual(preview.count, 1)
        self.assertEqual(preview.operations[0][1].parent.name, 'Ελληνικά')
        renamed, log = execute_preview(preview)
        self.assertEqual(renamed, 1)
        self.assertTrue((self.folder / 'Ελληνικά/Mousiki.mp3').is_file())
        self.assertEqual(restore_log(self.folder, log), (1, 1))

    def test_recursive_with_folder_names_on(self):
        self.touch('Ελληνικά/Μουσική.mp3')
        preview = create_preview(self.folder, recursive=True, rename_folders=True)
        self.assertEqual(preview.count, 2)
        renamed, log = execute_preview(preview)
        self.assertEqual(renamed, 2)
        self.assertTrue((self.folder / 'Ellinika/Mousiki.mp3').exists())
        self.assertEqual(restore_log(self.folder, log), (2, 2))

    def test_options_require_recursion_for_folder_names(self):
        self.touch('Ελληνικά/Μουσική.mp3')
        preview = create_preview(self.folder, recursive=False, rename_folders=True)
        self.assertFalse(preview.rename_folders)
        self.assertEqual(preview.count, 0)

    def test_stale_preview_rejected_with_no_changes(self):
        old = self.touch('Ελληνικά.mp3')
        preview = create_preview(self.folder, recursive=False, rename_folders=False)
        old.rename(self.folder / 'AlreadyEnglish.mp3')
        with self.assertRaises(PreviewChangedError):
            execute_preview(preview)
        self.assertEqual(list(self.folder.glob('greeklish_rename_log_*.csv')), [])

    def test_new_conflict_invalidates_preview(self):
        self.touch('Ελληνικά.mp3')
        preview = create_preview(self.folder, recursive=False, rename_folders=False)
        self.touch('Ellinika.mp3', b'protected')
        with self.assertRaises(PreviewChangedError):
            execute_preview(preview)
        self.assertEqual((self.folder / 'Ellinika.mp3').read_bytes(), b'protected')
        fresh = create_preview(self.folder, recursive=False, rename_folders=False)
        self.assertEqual(fresh.operations[0][1].name, 'Ellinika (2).mp3')

    def test_csv_undo_log_written(self):
        self.touch('Γεια.txt')
        preview = create_preview(self.folder, recursive=False, rename_folders=False)
        count, log = execute_preview(preview)
        self.assertEqual(count, 1)
        with log.open('r', encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['old_relative_path'], 'Γεια.txt')

    def test_symlink_folder_rejected(self):
        target = self.folder / 'real'; target.mkdir()
        shortcut = self.folder / 'shortcut'
        try:
            shortcut.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest('Creating symlinks requires elevated permissions here')
        with self.assertRaises(ValueError):
            create_preview(shortcut, recursive=True, rename_folders=True)


if __name__ == '__main__':
    unittest.main()

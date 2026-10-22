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



class GUISelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)

    def put(self, name: str, content: bytes = b'original'):
        p = self.folder / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return p

    def preview(self, *, recursive=False, rename_folders=False):
        return create_preview(self.folder, recursive=recursive, rename_folders=rename_folders)

    def test_selected_subset_skips_file_and_undo(self):
        self.put('Ελληνικά.mp3', b'greek')
        self.put('Αθήνα.mp3', b'athens')
        p = self.preview()
        self.assertEqual(p.count, 2)
        selected = (p.operations[0],)
        n, log = execute_preview(p, selected=selected)
        self.assertEqual(n, 1)
        skipped = ({old for old, new in p.operations} - {selected[0][0]}).pop()
        self.assertTrue(skipped.exists())
        self.assertEqual(skipped.read_bytes(), b'athens' if skipped.name == 'Αθήνα.mp3' else b'greek')
        self.assertEqual(restore_log(self.folder, log), (1, 1))
        self.assertTrue((self.folder/'Ελληνικά.mp3').exists())
        self.assertTrue((self.folder/'Αθήνα.mp3').exists())

    def test_manually_edited_name_and_undo(self):
        old = self.put('Ελληνικά.mp3', b'same bytes')
        p = self.preview()
        renamed_to = old.with_name('My Greek Music.mp3')
        n, log = execute_preview(p, selected=((old, renamed_to),))
        self.assertEqual(n, 1)
        self.assertEqual(renamed_to.read_bytes(), b'same bytes')
        self.assertEqual(restore_log(self.folder, log), (1, 1))
        self.assertEqual(old.read_bytes(), b'same bytes')

    def test_empty_selection_cannot_create_log(self):
        self.put('Ελληνικά.mp3')
        with self.assertRaisesRegex(Exception, 'No rows selected'):
            execute_preview(self.preview(), selected=())
        self.assertEqual(list(self.folder.glob('greeklish_rename_log_*.csv')), [])

    def test_manual_destination_existing_latin_name_rejected(self):
        self.put('Ελληνικά.mp3')
        self.put('Existing.mp3', b'untouched')
        p = self.preview()
        with self.assertRaisesRegex(Exception, 'already in use'):
            execute_preview(p, selected=((p.operations[0][0], self.folder/'Existing.mp3'),))
        self.assertEqual((self.folder/'Existing.mp3').read_bytes(), b'untouched')
        self.assertEqual(list(self.folder.glob('greeklish_rename_log_*.csv')), [])

    def test_manual_duplicate_destinations_rejected(self):
        self.put('Αθήνα.mp3')
        self.put('Ελληνικά.mp3')
        p = self.preview()
        chosen = ((p.operations[0][0], p.operations[0][0].with_name('Same.mp3')),
                  (p.operations[1][0], p.operations[1][0].with_name('same.MP3')))
        with self.assertRaisesRegex(Exception, 'same proposed name'):
            execute_preview(p, selected=chosen)
        self.assertEqual(list(self.folder.glob('greeklish_rename_log_*.csv')), [])

    def test_manual_destination_other_directory_rejected(self):
        self.put('Ελληνικά.mp3')
        p = self.preview()
        with self.assertRaisesRegex(Exception, 'filename only'):
            execute_preview(p, selected=((p.operations[0][0], self.folder/'other'/'new.mp3'),))

    def test_manual_source_not_in_preview_rejected(self):
        self.put('Ελληνικά.mp3')
        p = self.preview()
        with self.assertRaisesRegex(Exception, 'Unknown or duplicate'):
            execute_preview(p, selected=((self.folder/'Nope.mp3',self.folder/'Another.mp3'),))

    def test_manual_changed_source_preview_rejected(self):
        old = self.put('Ελληνικά.mp3')
        p = self.preview()
        old.rename(self.folder/'Else.mp3')
        with self.assertRaises(PreviewChangedError):
            execute_preview(p, selected=((old, old.with_name('Mine.mp3')),))

    def test_manual_new_conflict_after_preview_rejected(self):
        self.put('Ελληνικά.mp3')
        p = self.preview()
        self.put('Mine.mp3', b'protected')
        with self.assertRaisesRegex(Exception, 'already in use'):
            execute_preview(p, selected=((p.operations[0][0], self.folder/'Mine.mp3'),))
        self.assertEqual((self.folder/'Mine.mp3').read_bytes(), b'protected')

    def test_unchecked_child_inside_selected_folder_rejected(self):
        self.put('Ελληνικά/Τραγούδι.mp3')
        p = self.preview(recursive=True, rename_folders=True)
        self.assertEqual(p.count,2)
        folder_operations = tuple(op for op in p.operations if op[0].is_dir())
        with self.assertRaisesRegex(Exception, 'unchecked item'):
            execute_preview(p, selected=folder_operations)
        self.assertTrue((self.folder/'Ελληνικά/Τραγούδι.mp3').exists())

    def test_select_child_but_skip_parent_folder(self):
        self.put('Ελληνικά/Τραγούδι.mp3', b'good')
        p = self.preview(recursive=True, rename_folders=True)
        only_child = tuple(op for op in p.operations if op[0].is_file())
        n, log = execute_preview(p, selected=only_child)
        self.assertEqual(n, 1)
        self.assertTrue((self.folder/'Ελληνικά/Tragoudi.mp3').exists())
        self.assertFalse((self.folder/'Ellinika').exists())
        self.assertEqual(restore_log(self.folder, log), (1,1))

    def test_selected_folder_and_child_manual_name(self):
        old = self.put('Ελληνικά/Τραγούδι.mp3', b'good')
        p = self.preview(recursive=True, rename_folders=True)
        edit = tuple((source, old.with_name('Custom Song.mp3')) if source.name == old.name else (source,target)
                     for source,target in p.operations)
        n, log = execute_preview(p, selected=edit)
        self.assertEqual(n,2)
        self.assertEqual((self.folder/'Ellinika/Custom Song.mp3').read_bytes(), b'good')
        self.assertEqual(restore_log(self.folder,log),(2,2))
        self.assertTrue(old.exists())

    def test_no_silent_renames_of_unchecked_files(self):
        self.put('Ελληνικά.mp3')
        self.put('Αθήνα.mp3')
        self.put('English.txt')
        p=self.preview()
        n, log = execute_preview(p, selected=(p.operations[1],))
        self.assertEqual(n,1)
        self.assertTrue(p.operations[0][0].exists())
        self.assertTrue((self.folder/'English.txt').exists())
        self.assertEqual(restore_log(self.folder,log),(1,1))

    def test_bad_windows_names(self):
        from renamer_service import validate_new_filename, InvalidSelectionError
        for value in ('', '.', '..', 'x?', 'bad/name', 'bad\\name', 'bad:name',
                      'x.', 'x ', 'CON', 'aux.txt', 'COM1.mp3', 'LPT9', 'nUl.dat',
                      'Ελληνικά.mp3', 'A'*256+'.mp3'):
            with self.subTest(value=value), self.assertRaises(InvalidSelectionError):
                validate_new_filename(value, original='Ελληνικά.mp3')
        validate_new_filename('Greek (manual).mp3', original='Ελληνικά.mp3')

    def test_case_insensitive_existing_collision(self):
        self.put('Ελληνικά.mp3')
        self.put('My Music.mp3')
        p=self.preview()
        with self.assertRaisesRegex(Exception, 'already in use'):
            execute_preview(p, selected=((p.operations[0][0], self.folder/'my music.MP3'),))

    def test_sibling_source_cannot_be_used_as_destination(self):
        self.put('Ελληνικά.mp3')
        self.put('Αθήνα.mp3')
        p=self.preview()
        with self.assertRaisesRegex(Exception, 'already in use'):
            execute_preview(p, selected=((p.operations[0][0], p.operations[1][0]),))

    def test_edited_selection_plan_is_restored_in_original_order(self):
        self.put('Ελληνικά/Τραγούδι.mp3')
        p=self.preview(recursive=True, rename_folders=True)
        reversed_ops = tuple(reversed(p.operations))
        n, log = execute_preview(p, selected=reversed_ops)
        self.assertEqual(n,2)
        self.assertTrue((self.folder/'Ellinika/Tragoudi.mp3').exists())
        self.assertEqual(restore_log(self.folder,log),(2,2))

if __name__ == '__main__':
    unittest.main()

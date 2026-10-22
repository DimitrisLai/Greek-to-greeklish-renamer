"""Regressions for local preferences and non-destructive cooperative scan cancellation."""
from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from rename_greek_to_greeklish import ScanCancelled, plan_renames
from renamer_service import create_preview, execute_preview, restore_log
from user_preferences import Preferences, load, save, safe_folder, sanitize, settings_path


class PreferenceTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.settings = self.root / 'config' / 'settings.json'

    def test_empty_initial_settings(self):
        self.assertEqual(load(self.settings), Preferences())

    def test_saved_folder_and_filter_survive_restart(self):
        expected = Preferences(str(self.root.resolve()), 'MP3 only', '.mp3, .FLAC')
        self.assertTrue(save(expected, self.settings))
        self.assertEqual(load(self.settings).last_folder, str(self.root.resolve()))
        self.assertEqual(load(self.settings).file_type_preset, 'MP3 only')
        self.assertEqual(load(self.settings).custom_file_types, '.mp3, .FLAC')
        self.assertEqual(json.loads(self.settings.read_text())['schema_version'], 1)
        self.assertFalse(list(self.settings.parent.glob('*.tmp')))

    def test_custom_selection_survives_restart(self):
        expected = Preferences(str(self.root), 'Custom list…', '.wav, .flac')
        self.assertTrue(save(expected, self.settings))
        self.assertEqual(load(self.settings).file_type_preset, 'Custom list…')

    def test_untrusted_or_malformed_values_rejected(self):
        self.settings.parent.mkdir()
        self.settings.write_text('{invalid JSON', encoding='utf-8')
        self.assertEqual(load(self.settings), Preferences())
        for raw in [None, [], {'file_type_preset': 'Unknown', 'custom_file_types': '*.bad, ?' , 'last_folder': '../../absent'},
                    {'last_folder': 42, 'file_type_preset': 5, 'custom_file_types': None}]:
            sanitized = sanitize(raw)
            self.assertEqual(sanitized.file_type_preset, 'All file types')
            self.assertEqual(sanitized.last_folder, '')
            self.assertEqual(sanitized.custom_file_types, '.mp3, .flac')

    def test_oversize_file_does_not_load(self):
        self.settings.parent.mkdir()
        self.settings.write_bytes(b' ' * 17000)
        self.assertEqual(load(self.settings), Preferences())

    def test_missing_folder_is_not_restored(self):
        expected = Preferences(str(self.root / 'not-there'), 'WAV only', '.wav')
        self.assertTrue(save(expected, self.settings))
        self.assertEqual(load(self.settings).last_folder, '')
        self.assertEqual(load(self.settings).file_type_preset, 'WAV only')

    def test_symlink_path_not_restored(self):
        alias = self.root / 'linked'
        try:
            alias.symlink_to(self.root, target_is_directory=True)
        except OSError:
            self.skipTest('symlink permissions unavailable')
        self.assertEqual(safe_folder(str(alias)), '')

    def test_settings_are_in_app_config_directory(self):
        self.assertEqual(settings_path(home=self.root), self.root/'GreeklishRenamer'/'settings.json')

    def test_empty_save_does_not_destroy_previous_when_exception(self):
        expected = Preferences(str(self.root), 'FLAC only', '.flac')
        self.assertTrue(save(expected, self.settings))
        with patch('user_preferences.os.replace', side_effect=PermissionError('access denied')):
            self.assertFalse(save(Preferences(str(self.root), 'MP3 only', '.mp3'), self.settings))
        self.assertEqual(load(self.settings).file_type_preset, 'FLAC only')


class ScanCancellationTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        for i in range(200):
            (self.root/f'Αρχείο {i:04}.mp3').write_bytes(bytes([i % 256]))

    def assert_unchanged(self):
        self.assertEqual(len(list(self.root.glob('*.mp3'))), 200)
        self.assertEqual(len(list(self.root.glob('greeklish_rename_log*'))), 0)

    def test_cancel_before_nonrecursive_scan(self):
        with self.assertRaises(ScanCancelled):
            create_preview(self.root, recursive=False, rename_folders=False,
                           should_cancel=lambda: True)
        self.assert_unchanged()

    def test_cancel_during_nonrecursive_iteration(self):
        calls = 0
        def signal():
            nonlocal calls
            calls += 1
            return calls > 2
        with self.assertRaises(ScanCancelled):
            create_preview(self.root, recursive=False, rename_folders=False,
                           should_cancel=signal)
        self.assert_unchanged()

    def test_cancel_via_progress_callback_on_recursive_tree(self):
        (self.root/'Nested').mkdir()
        (self.root/'Nested'/'Ελληνικά.flac').write_bytes(b'x')
        event = threading.Event()
        seen = []
        def progress(folders, files, current):
            seen.append((folders, files, current))
            event.set()
        with self.assertRaises(ScanCancelled):
            create_preview(self.root, recursive=True, rename_folders=False,
                           scan_progress=progress, should_cancel=event.is_set)
        self.assertGreaterEqual(len(seen), 1)
        self.assert_unchanged()
        self.assertTrue((self.root/'Nested'/'Ελληνικά.flac').exists())

    def test_cancel_near_end_of_processing_plan(self):
        calls = 0
        def signal():
            nonlocal calls
            calls += 1
            return calls >= 4
        with self.assertRaises(ScanCancelled):
            plan_renames(self.root, should_cancel=signal)
        self.assert_unchanged()

    def test_cancelled_scan_followed_by_fresh_preview_and_undo(self):
        with self.assertRaises(ScanCancelled):
            create_preview(self.root, recursive=False, rename_folders=False,
                           should_cancel=lambda: True)
        preview = create_preview(self.root, recursive=False, rename_folders=False)
        self.assertEqual(preview.count, 200)
        selected = preview.operations[:3]
        changed, logfile = execute_preview(preview, selected=selected)
        self.assertEqual(changed, 3)
        self.assertEqual(restore_log(self.root, logfile), (3, 3))
        self.assertEqual(len(list(self.root.glob('*.mp3'))), 200)
        self.assertTrue(logfile.is_file())


if __name__ == '__main__':
    unittest.main()

"""v2.2: filter safety, scan callbacks, Explorer menus, and metadata checks."""
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import explorer_integration as explorer
from rename_greek_to_greeklish import plan_renames
from renamer_service import (create_preview, execute_preview_report,
                             normalize_extensions, parse_extensions, restore_log)


class FilterTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)

    def put(self, name, payload=b'KEEP DATA'):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(payload)
        return p

    def test_all_types_remains_default(self):
        self.put('Ελληνικά.mp3')
        self.put('Αθήνα.flac')
        self.put('Κόσμος.txt')
        p = create_preview(self.root, recursive=False, rename_folders=False)
        self.assertEqual(p.count, 3)
        self.assertEqual(p.file_extensions, ())

    def test_only_mp3_case_insensitive(self):
        self.put('Ελληνικά.MP3')
        self.put('Αθήνα.flac')
        self.put('Κόσμος.wav')
        self.put('Already English.mp3')
        p = create_preview(self.root, recursive=False, rename_folders=False,
                           file_extensions=('.Mp3',))
        self.assertEqual([o.name for o, _ in p.operations], ['Ελληνικά.MP3'])
        self.assertEqual(p.file_extensions, ('.mp3',))

    def test_combined_extensions_and_recursive(self):
        self.put('Μουσική/Τραγούδι.MP3')
        self.put('Μουσική/Άλλο.flac')
        self.put('Μουσική/Μέμο.txt')
        p = create_preview(self.root, recursive=True, rename_folders=False,
                           file_extensions=['.flac', '.MP3'])
        self.assertEqual(p.count, 2)
        self.assertTrue(all(old.is_file() for old, _ in p.operations))
        report = execute_preview_report(p, p.operations)
        self.assertEqual(report.renamed_count, 2)
        self.assertEqual((self.root/'Μουσική/Μέμο.txt').read_bytes(), b'KEEP DATA')
        self.assertTrue((self.root/'Μουσική').is_dir())
        self.assertEqual(restore_log(self.root, report.log), (2, 2))

    def test_filtered_folder_renames_rejected(self):
        self.put('Μουσική/Άλλο.mp3')
        with self.assertRaisesRegex(ValueError, 'Folder renaming'):
            create_preview(self.root, recursive=True, rename_folders=True,
                           file_extensions=['.mp3'])

    def test_no_filter_folder_renames_still_supported(self):
        self.put('Μουσική/Άλλο.mp3')
        p = create_preview(self.root, recursive=True, rename_folders=True)
        self.assertEqual(p.folder_count, 1)
        self.assertEqual(p.file_count, 1)

    def test_filter_rules_remain_in_stale_preview(self):
        a = self.put('Τραγούδι.mp3')
        self.put('Κόσμος.txt')
        p = create_preview(self.root, recursive=False, rename_folders=False,
                           file_extensions=['.mp3'])
        self.assertEqual(p.count, 1)
        report = execute_preview_report(p, p.operations)
        self.assertEqual(report.renamed_count, 1)
        self.assertTrue((self.root/'Κόσμος.txt').exists())
        restore_log(self.root, report.log)
        self.assertTrue(a.exists())

    def test_scan_reports_folders_and_files_without_guessing_total(self):
        self.put('Ελληνικά/Τραγούδι.mp3')
        self.put('Other/Όνομα.flac')
        self.put('Other/English.txt')
        updates = []
        p = create_preview(self.root, recursive=True, rename_folders=False,
                           scan_progress=lambda dirs, files, path: updates.append((dirs, files, path)))
        self.assertEqual(p.count, 2)
        self.assertEqual(len(updates), 3)
        self.assertEqual([x[0] for x in updates], [1, 2, 3])
        self.assertEqual(updates[-1][1], 3)
        self.assertEqual(updates[0][2].resolve(), self.root.resolve())

    def test_nonrecursive_scan_reports_once(self):
        self.put('Άλλο.mp3')
        self.put('nested/Τραγούδι.mp3')
        updates = []
        plan_renames(self.root, scan_progress=lambda *data: updates.append(data))
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0][1], 1)

    def test_normalization(self):
        self.assertEqual(parse_extensions(' *.MP3 ;flac, .WAV '), ('.flac', '.mp3', '.wav'))
        self.assertEqual(normalize_extensions(None), ())
        self.assertEqual(normalize_extensions(['mp3','.mp3']), ('.mp3',))

    def test_reject_empty_invalid_and_path_filters(self):
        for text in ('', ' ', '/etc/passwd', '.mp?', '*.ex*', '.exe/../../../'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_extensions(text)


class ExplorerContractTests(unittest.TestCase):
    def test_directory_and_background_commands_are_preview_only(self):
        self.assertEqual(len(explorer.KEYS), 2)
        for key, placeholder in explorer.KEYS:
            command = explorer.launch_command(r'C:\Program Files\Greeklish\GreeklishRenamer.exe', placeholder)
            self.assertIn('--folder', command)
            self.assertNotIn('--yes', command)
            self.assertNotIn('--apply', command)
            self.assertIn(f'"{placeholder}"', command)
            self.assertIn('Directory', key)

    def test_reject_unexpected_placeholder(self):
        with self.assertRaises(ValueError):
            explorer.launch_command('GreeklishRenamer.exe', '%*')

    def test_non_windows_registry_denied(self):
        with patch.object(explorer, 'available', return_value=False):
            with self.assertRaises(OSError):
                explorer.unregister()
            with self.assertRaises(OSError):
                explorer.register('GreeklishRenamer.exe')

    def test_no_registry_change_during_module_import(self):
        # Pure functions and constants; user must explicitly invoke register().
        self.assertEqual(explorer.MENU_NAME, 'GreeklishRenamer')
        self.assertTrue(all(x.startswith('Software\\Classes\\') for x, _ in explorer.KEYS))


class PackagingContractTests(unittest.TestCase):
    def test_icon_and_version_resource_present(self):
        root = Path(__file__).resolve().parents[1]
        self.assertTrue((root/'scripts/generate_icon.py').is_file())
        self.assertIn('Pillow', (root/'.github/workflows/release-v2.3.0.yml').read_text('utf-8'))
        metadata=(root/'packaging/windows_version_info.txt').read_text('utf-8')
        for value in ('Greek to Greeklish Renamer', '2.3.0.0', 'Dimitris Laidis'):
            self.assertIn(value, metadata)

    def test_release_checksum_rules_present(self):
        root=Path(__file__).resolve().parents[1]
        flow=(root/'.github/workflows/release-v2.3.0.yml').read_text('utf-8')
        for value in ('--icon', '--version-file', 'SHA256SUMS.txt', 'sha256sum -c'):
            self.assertIn(value, flow)


if __name__ == '__main__':
    unittest.main()


class RegistryMockTests(unittest.TestCase):
    def test_install_then_remove_only_own_registry_entries(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / 'GreeklishRenamer.exe'
            exe.write_bytes(b'mock, no real exe')
            reg = SimpleNamespace(
                HKEY_CURRENT_USER=object(), KEY_WRITE=0x20006, REG_SZ=1,
                CreateKeyEx=MagicMock(), SetValueEx=MagicMock(), DeleteKey=MagicMock())
            with patch.object(explorer, 'available', return_value=True), patch.dict(sys.modules, {'winreg': reg}):
                explorer.register(exe)
                self.assertEqual(reg.CreateKeyEx.call_count, 4)
                self.assertEqual(reg.SetValueEx.call_count, 6)
                # Ensure only explicit command values embed the launched executable.
                commands = [c.args[4] for c in reg.SetValueEx.call_args_list if c.args[1] == '']
                self.assertEqual(len(commands), 2)
                self.assertTrue(all('--folder' in cmd and '--yes' not in cmd for cmd in commands))
                explorer.unregister()
                self.assertEqual(reg.DeleteKey.call_count, 4)
                paths = [call.args[1] for call in reg.DeleteKey.call_args_list]
                self.assertTrue(all('GreeklishRenamer' in path for path in paths))

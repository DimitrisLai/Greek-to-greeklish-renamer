"""v2.1.2 regression coverage: controlled stop, reports, extension lock, subset."""
import csv
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from renamer_service import (
    InvalidSelectionError, create_preview, execute_preview_report,
    validate_new_filename, validate_selection, restore_log,
)
from rename_greek_to_greeklish import apply_plan


class BatchSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def add(self, name, content=b'same bytes'):
        p = self.root / name
        p.parent.mkdir(exist_ok=True, parents=True)
        p.write_bytes(content)
        return p

    def preview(self, recursive=False, rename_folders=False):
        return create_preview(self.root, recursive=recursive, rename_folders=rename_folders)

    def test_unchanged_extension_is_allowed(self):
        validate_new_filename('Custom.mp3', original='Ελληνικά.mp3')

    def test_extension_change_requires_opt_in(self):
        with self.assertRaisesRegex(InvalidSelectionError, 'extension is protected'):
            validate_new_filename('Custom.wav', original='Ελληνικά.mp3')
        validate_new_filename('Custom.wav', original='Ελληνικά.mp3', allow_extension_change=True)

    def test_extension_change_is_enforced_by_backend(self):
        old = self.add('Ελληνικά.mp3')
        p = self.preview()
        selected = ((old, old.with_name('Custom.wav')),)
        with self.assertRaisesRegex(InvalidSelectionError, 'extension is protected'):
            execute_preview_report(p, selected)
        self.assertEqual(list(self.root.glob('greeklish_rename_log_*.csv')), [])
        report = execute_preview_report(p, selected, extension_overrides={old})
        self.assertEqual(report.renamed_count, 1)
        self.assertEqual((self.root/'Custom.wav').read_bytes(), b'same bytes')
        self.assertEqual(restore_log(self.root, report.log), (1, 1))

    def test_extension_override_accepts_equivalent_path_alias(self):
        original = self.add('Ελληνικά.mp3')
        preview = self.preview()
        # An equivalent but unnormalized spelling reproduces Windows' short
        # vs long temp path discrepancy without requiring a Windows runner.
        equivalent = original.parent / '..' / original.parent.name / original.name
        report = execute_preview_report(preview,
            ((original,original.with_name('Custom.wav')),),
            extension_overrides={equivalent})
        self.assertEqual(report.renamed_count, 1)
        self.assertTrue((self.root/'Custom.wav').exists())
        self.assertEqual(restore_log(self.root, report.log), (1, 1))

    def test_folder_dots_are_not_treated_as_extensions(self):
        self.add('Μουσική.2026/Τραγούδι.mp3')
        p = self.preview(recursive=True, rename_folders=True)
        edit = tuple((src, src.with_name('Album.2026')) if src.is_dir() else (src, dest)
                     for src, dest in p.operations)
        report = execute_preview_report(p, edit)
        self.assertEqual(report.renamed_count, 2)
        self.assertTrue((self.root/'Album.2026'/'Tragoudi.mp3').exists())

    def test_results_include_excluded_item_and_durable_csv(self):
        first = self.add('Ελληνικά.mp3', b'first')
        second = self.add('Αθήνα.mp3', b'second')
        p = self.preview()
        report = execute_preview_report(p, ((first, first.with_name('My name.mp3')),))
        self.assertEqual((report.renamed_count, report.skipped_count, report.failed_count,
                          report.excluded_count, report.remaining_count), (1, 0, 0, 1, 0))
        self.assertTrue(second.exists())
        self.assertIsNotNone(report.report_file)
        with report.report_file.open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        self.assertEqual({r['status'] for r in rows}, {'renamed','excluded'})
        self.assertTrue(any(r['reason'] == 'Unchecked in the preview' for r in rows))
        self.assertEqual(restore_log(self.root, report.log), (1,1))

    def test_stop_between_operations_preserves_undo(self):
        for n in range(120):
            self.add(f'Αρχείο {n:03d}.txt', str(n).encode())
        preview = self.preview()
        flag = {'stop': False}
        updates = []
        def on_progress(done, total, renamed):
            updates.append((done,total,renamed))
            if done == 29:
                flag['stop'] = True
        report = execute_preview_report(preview, preview.operations,
                           stop_requested=lambda: flag['stop'], progress_callback=on_progress)
        self.assertTrue(report.stopped)
        self.assertEqual(report.selected_count, 120)
        self.assertEqual(report.renamed_count, 29)
        self.assertEqual(report.remaining_count, 91)
        self.assertEqual((report.skipped_count, report.failed_count), (0,0))
        self.assertEqual(updates[-1], (29,120,29))
        self.assertEqual(sum(r.status=='not processed' for r in report.rows), 91)
        self.assertTrue(report.report_file.is_file())
        self.assertEqual(restore_log(self.root, report.log), (29,29))
        self.assertEqual(len(list(self.root.glob('Αρχείο *.txt'))),120)

    def test_stop_with_folder_descendants_undo_safe(self):
        self.add('Ελληνικά/Τραγούδι.mp3')
        p = self.preview(recursive=True, rename_folders=True)
        requested = {'stop':False}
        def report(done, total, renamed):
            requested['stop'] = True
        run = execute_preview_report(p, p.operations,
                        stop_requested=lambda:requested['stop'], progress_callback=report)
        self.assertEqual((run.renamed_count,run.remaining_count),(1,1))
        self.assertTrue((self.root/'Ελληνικά'/'Tragoudi.mp3').exists())
        self.assertEqual(restore_log(self.root, run.log),(1,1))
        self.assertTrue((self.root/'Ελληνικά'/'Τραγούδι.mp3').exists())

    def test_skip_and_fail_reasons_are_captured(self):
        a=self.add('Ελληνικά.mp3'); b=self.add('Αθήνα.mp3'); c=self.add('Κόσμος.mp3')
        actions=[(a, self.root/'Ellinika.mp3'),
                 (b,self.root/'Athina.mp3'),
                 (c,self.root/'Kosmos.mp3')]
        (self.root/'Athina.mp3').write_bytes(b'occupied')
        old_rename=Path.rename
        def rename(path,destination):
            if path == c:
                raise PermissionError('locked by music player')
            return old_rename(path,destination)
        with mock.patch('pathlib.Path.rename', autospec=True, side_effect=rename):
            done=[]
            with redirect_stdout(io.StringIO()):
                n,log=apply_plan(self.root,actions,result_callback=lambda *args: done.append(args))
        self.assertEqual(n,1)
        self.assertEqual([x[2] for x in done],['renamed','skipped','failed'])
        self.assertIn('already occupied',done[1][3])
        self.assertIn('locked by music player',done[2][3])
        with log.open(encoding='utf-8-sig',newline='') as handle:
            self.assertEqual(len(list(csv.DictReader(handle))), 1)

    def test_progress_reporting_callback_cannot_interrupt_undo(self):
        p=self.add('Ελληνικά.mp3')
        def buggy_callback(*args):
            raise RuntimeError('simulated UI callback failure')
        with redirect_stdout(io.StringIO()):
            n,log=apply_plan(self.root,[(p,p.with_name('Ellinika.mp3'))],
                            progress_callback=buggy_callback,result_callback=buggy_callback)
        self.assertEqual(n,1)
        self.assertEqual(restore_log(self.root,log),(1,1))

if __name__=='__main__':
    unittest.main()

"""Progress and large-batch tests for the Windows GUI rename engine."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from renamer_service import create_preview, execute_preview, restore_log
from rename_greek_to_greeklish import apply_plan

class ProgressRegressionTests(unittest.TestCase):
    def test_thousand_names_progress_and_undo(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for i in range(1000):
                (root/f'Αρχείο {i:04}.txt').write_bytes(f'CONTENT-{i}'.encode())
            (root/'English.txt').write_bytes(b'DO NOT TOUCH')
            preview=create_preview(root,recursive=False,rename_folders=False)
            self.assertEqual(preview.count,1000)
            callbacks=[]
            selected=tuple(op for index,op in enumerate(preview.operations) if index%2==0)
            changed, log=execute_preview(preview,selected=selected,
                           progress_callback=lambda done,total,renamed:callbacks.append((done,total,renamed)))
            self.assertEqual(changed,500)
            self.assertEqual(len(callbacks),500)
            self.assertEqual(callbacks[0],(1,500,1))
            self.assertEqual(callbacks[-1],(500,500,500))
            self.assertEqual([row[0] for row in callbacks],list(range(1,501)))
            self.assertEqual((root/'English.txt').read_bytes(),b'DO NOT TOUCH')
            for index,(old,new) in enumerate(preview.operations):
                if index%2:
                    self.assertTrue(old.exists(),str(old))
                    self.assertFalse(new.exists(),str(new))
                else:
                    self.assertFalse(old.exists(),str(old))
                    self.assertTrue(new.exists(),str(new))
            restored,total=restore_log(root,log)
            self.assertEqual((restored,total),(500,500))
            self.assertEqual(len(list(root.glob('Αρχείο *.txt'))),1000)

    def test_skipped_operation_still_advances_progress(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            missing=root/'does_not_exist.txt'
            original=root/'Αθήνα.txt'
            original.write_bytes(b'original')
            status=[]
            processed,log=apply_plan(root,[(missing,root/'new.txt'),(original,root/'Athina.txt')],
                progress_callback=lambda done,total,renamed:status.append((done,total,renamed)))
            self.assertEqual(processed,1)
            self.assertEqual(status,[(1,2,0),(2,2,1)])
            self.assertTrue(log.is_file())

    def test_callback_optional_for_existing_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            old=root/'Τραγούδι.mp3';old.write_bytes(b'audio')
            n, log=apply_plan(root,[(old,root/'Tragoudi.mp3')])
            self.assertEqual(n,1)
            self.assertTrue(log.exists())

if __name__=='__main__':
    unittest.main()

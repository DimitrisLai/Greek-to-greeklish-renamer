from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rename_greek_to_greeklish import ScanCancelled
from renamer_service import create_preview,execute_preview_report,restore_log

with TemporaryDirectory() as tmp:
    root=Path(tmp);folders=25;per=80
    for i in range(folders):
        d=root/f'Music_{i:02}';d.mkdir()
        for j in range(per):
            (d/f'Ελληνικά {j:03}.mp3').write_bytes(b'MUSIC'*5)
            (d/f'Ελληνικά {j:03}.txt').write_bytes(b'TEXT'*5)
    inspected=[];event=Event()
    def report(f,n,current):
        inspected.append((f,n))
        if f>=13:event.set()
    try:
        create_preview(root,recursive=True,rename_folders=False,file_extensions=['.mp3'],scan_progress=report,should_cancel=event.is_set)
        raise AssertionError('Expected cancellation')
    except ScanCancelled:pass
    assert not list(root.rglob('greeklish_rename_log*.csv'))
    assert sum(1 for _ in root.rglob('*.mp3'))==2000
    scanned=[]
    p=create_preview(root,recursive=True,rename_folders=False,file_extensions=['.mp3'],scan_progress=lambda f,n,d:scanned.append((f,n)))
    assert p.count==2000,p.count
    assert scanned[-1]==(26,4000),scanned[-1]
    part=p.operations[:250]
    done=execute_preview_report(p,part)
    assert done.renamed_count==250 and done.failed_count==0
    assert sum(1 for _ in root.rglob('*.txt'))==2000
    assert restore_log(root,done.log)==(250,250)
    assert sum(1 for _ in root.rglob('*.mp3'))==2000
    print('PASS STRESS: 4,000 files / 26 folders scanned, cancel at folder 13 without changes, 2,000 eligible MP3 files, rename and undo 250, 2,000 TXT files untouched')

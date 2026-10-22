"""Build official source and Windows ZIP archives, including the complete manual."""
from __future__ import annotations
import argparse
import subprocess
import zipfile
from pathlib import Path

VERSION='2.1.2'
MANUAL=f'Greek_to_Greeklish_Renamer_User_Manual_v{VERSION}_Dimitris_Laidis.pdf'
WINDOWS=f'Greeklish-Renamer-v{VERSION}-Windows-Dimitris-Laidis.zip'
SOURCE=f'Greeklish-Renamer-v{VERSION}-Source-Dimitris-Laidis.zip'


def build(output:Path, exe:Path|None):
    root=Path(__file__).resolve().parents[1]
    output.mkdir(parents=True,exist_ok=True)
    pdf=output/MANUAL
    if not pdf.is_file():
        raise FileNotFoundError('Build the PDF manual first: '+str(pdf))
    if exe is not None:
        if not exe.is_file():
            raise FileNotFoundError('Windows EXE not found: '+str(exe))
        with zipfile.ZipFile(output/WINDOWS,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name in ('LICENSE','README_FIRST.txt'):
                z.write(root/name,name)
            z.write(exe,'GreeklishRenamer.exe')
            z.write(pdf,MANUAL)
    raw=subprocess.check_output(['git','ls-files','-z'],cwd=root)
    tracked=[name.decode('utf-8') for name in raw.split(b'\0') if name]
    with zipfile.ZipFile(output/SOURCE,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for filename in tracked:
            if filename.lower().endswith('.pdf'):
                continue
            z.write(root/filename,filename)
        z.write(pdf,'docs/'+MANUAL)
    for path in (output/WINDOWS,output/SOURCE):
        if not path.exists():continue
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                raise RuntimeError(f'Broken archive: {path}')
            assert MANUAL in ' '.join(z.namelist()),'Missing PDF'
        print(path, path.stat().st_size)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--exe',type=Path,default=None)
    args=ap.parse_args()
    build(args.output,args.exe)

"""Create final downloadable Windows and source ZIPs from the checkout."""
from pathlib import Path
import subprocess
import zipfile
import argparse

VERSION="1.2.1"
PDF="Greek_to_Greeklish_Renamer_User_Manual_v1.2.1_Dimitris_Laidis.pdf"
WIN="Greeklish-Renamer-v1.2.1-Windows-Dimitris-Laidis.zip"
SOURCE="Greeklish-Renamer-v1.2.1-Source-Dimitris-Laidis.zip"

def build(output):
    root=Path(__file__).resolve().parents[1]
    output.mkdir(parents=True,exist_ok=True)
    pdf=output/PDF
    if not pdf.is_file():
        raise FileNotFoundError(f"Build the manual first: {pdf}")
    windows=["rename_greek_to_greeklish.py","Run_Greek_to_Greeklish.cmd","AUTHOR.txt","LICENSE"]
    with zipfile.ZipFile(output/WIN,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in windows:
            z.write(root/name,name)
        z.write(pdf,PDF)
    raw=subprocess.check_output(["git","ls-files","-z"],cwd=root)
    tracked=[p.decode("utf-8") for p in raw.split(b"\0") if p]
    with zipfile.ZipFile(output/SOURCE,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in tracked:
            if name.startswith(".github/") or name.endswith(".pdf"):
                continue
            z.write(root/name,name)
        z.write(pdf,"docs/"+PDF)
    for zippath in (output/WIN,output/SOURCE):
        with zipfile.ZipFile(zippath) as z:
            if z.testzip() is not None:
                raise RuntimeError(f"ZIP validation failed: {zippath}")
        print(zippath, zippath.stat().st_size)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path("dist"))
    args=parser.parse_args()
    build(args.output)

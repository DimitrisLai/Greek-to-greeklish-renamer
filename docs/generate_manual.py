"""Build public PDF manual (release packaging only; the application has no dependencies)."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
import argparse

NAVY=HexColor("#122A40")
TEAL=HexColor("#0C7C86")
DARK=HexColor("#213547")
MUTED=HexColor("#526879")
LINE=HexColor("#DEE9ED")
PALE=HexColor("#F0F7F8")
WHITE=HexColor("#FFFFFF")
W,H=A4
L,R=54,W-54

def fonts():
    base=Path("/usr/share/fonts/truetype/dejavu")
    pdfmetrics.registerFont(TTFont("DV",str(base/"DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DVB",str(base/"DejaVuSans-Bold.ttf")))

def paragraph(c,s,y,size=9.3,width=470,leading=16,bold=False,color=DARK,x=None):
    p=Paragraph(s,ParagraphStyle("p",fontName="DVB" if bold else "DV",fontSize=size,
                                 leading=leading,textColor=color))
    _,height=p.wrap(width,250)
    p.drawOn(c,L if x is None else x,y-height)
    return y-height

def base(c,n):
    c.setFillColor(WHITE)
    c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(TEAL)
    c.rect(0,H-7,W,7,fill=1,stroke=0)
    c.setStrokeColor(LINE)
    c.line(L,58,R,58)
    c.setFillColor(MUTED)
    c.setFont("DV",7.4)
    c.drawString(L,41,"Greek to Greeklish Renamer  |  v1.2.1  |  Dimitris Laidis")
    c.drawRightString(R,41,str(n))

def box(c,y,height):
    c.setFillColor(PALE)
    c.roundRect(L,y-height,R-L,height,9,fill=1,stroke=0)

def section(c,label,title):
    c.setFillColor(TEAL); c.setFont("DVB",9)
    c.drawString(L,H-79,label)
    c.setFillColor(NAVY); c.setFont("DVB",20)
    c.drawString(L,H-112,title)
    c.setStrokeColor(LINE); c.line(L,H-130,R,H-130)
    return H-152

def heading(c,label,y):
    c.setFillColor(NAVY); c.setFont("DVB",11)
    c.drawString(L,y,label)
    return y-17

def build(dest):
    fonts()
    dest.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(dest),pagesize=A4,pageCompression=1)
    c.setTitle("Greek to Greeklish Renamer | User Manual v1.2.1")
    c.setAuthor("Dimitris Laidis")
    c.setSubject("Public user manual for Greek to Greeklish Renamer")
    # First page: clear cover + table of contents
    base(c,1)
    c.setFillColor(TEAL);c.setFont("DVB",9);c.drawString(L,H-83,"SOFTWARE USER MANUAL")
    c.setFillColor(NAVY);c.setFont("DVB",32)
    c.drawString(L,H-153,"Greek to Greeklish")
    c.drawString(L,H-196,"Renamer")
    c.setFillColor(MUTED);c.setFont("DV",11)
    c.drawString(L,H-226,"Rename files and folders safely, without changing their contents.")
    box(c,H-258,109)
    c.setFillColor(TEAL);c.setFont("DVB",9);c.drawString(L+17,H-283,"EXAMPLE CONVERSION")
    c.setFillColor(NAVY);c.setFont("DV",14);c.drawString(L+17,H-320,"Ελληνικά.mp3")
    c.setFillColor(TEAL);c.setFont("DVB",14);c.drawString(L+215,H-320,"→  Ellinika.mp3")
    c.setFillColor(MUTED);c.setFont("DV",8.6)
    c.drawString(L+17,H-345,"Only names containing Greek letters are considered for renaming.")
    y=paragraph(c,"What this manual includes",H-406,size=15,bold=True,color=NAVY,leading=20)-18
    sections=[
        ("01","Getting started","Install Python, choose a directory, preview changes","2"),
        ("02","Renaming rules and safety","Greek-only detection, folder options, conflict protection","3"),
        ("03","Undo and troubleshooting","Restore original names, commands, and common problems","4")
    ]
    for num,title,desc,page in sections:
        c.setStrokeColor(LINE);c.line(L,y+4,R,y+4)
        c.setFillColor(TEAL);c.setFont("DVB",10);c.drawString(L,y-14,num)
        c.setFillColor(NAVY);c.drawString(L+40,y-14,title)
        c.setFillColor(MUTED);c.setFont("DV",8.6);c.drawString(L+40,y-34,desc)
        c.setFillColor(TEAL);c.setFont("DVB",9);c.drawRightString(R,y-14,page)
        y-=63
    c.setFillColor(NAVY);c.setFont("DVB",10)
    c.drawString(L,105,"Created by Dimitris Laidis")
    c.setFillColor(MUTED);c.setFont("DV",8)
    c.drawString(L,88,"MIT License  |  Python 3.10+  |  Version 1.2.1")
    c.showPage()
    # Page 2: instructions
    base(c,2);y=section(c,"01 / QUICK START","Getting started")
    y=paragraph(c,"This lightweight Windows-friendly tool converts Greek filenames and folder names to Latin characters. It never changes file contents.",y)-23
    y=heading(c,"Requirements",y)
    y=paragraph(c,"Windows 10/11 and Python 3.10 or later. No additional Python libraries are required to run the renamer.",y)-27
    y=heading(c,"How to use it",y)
    steps=[
        "Extract the ZIP, keeping <b>rename_greek_to_greeklish.py</b> and <b>Run_Greek_to_Greeklish.cmd</b> together.",
        "Double-click <b>Run_Greek_to_Greeklish.cmd</b>.",
        "Paste or drag a folder into the window, or press Enter to use the script folder.",
        "Choose <b>Y</b> to include subdirectories or <b>N / Enter</b> for the selected folder only.",
        "Review the proposed changes. Type <b>YES</b> to apply, or anything else to cancel."
    ]
    for index,step in enumerate(steps,1):
        c.setFillColor(TEAL);c.setFont("DVB",10)
        c.drawString(L,y-11,f"{index:02}.")
        y=paragraph(c,step,y+1,width=R-L-45,x=L+42)-13
    y-=15
    box(c,y,99)
    c.setFillColor(TEAL);c.setFont("DVB",10)
    c.drawString(L+14,y-24,"BEFORE PROCESSING A LARGE FOLDER")
    paragraph(c,"Test with a few files first and back up important folders. Playlists and software referencing old paths may need updating.",y-36,width=435)
    c.showPage()
    # Page 3: examples and safety
    base(c,3);y=section(c,"02 / RENAME RULES","What changes and what stays")
    y=paragraph(c,"Only names containing Greek letters are candidates. Filenames already written in English/Greeklish remain unchanged.",y)-20
    box(c,y,182)
    c.setFillColor(NAVY);c.setFont("DVB",9)
    c.drawString(L+12,y-24,"ORIGINAL")
    c.drawString(L+230,y-24,"RESULT")
    rows=[
        ("Γιώργος Μαζωνάκης.mp3","Giorgos Mazonakis.mp3"),
        ("Δημήτρης Κόκοτας.flac","Dimitris Kokotas.flac"),
        ("DJ Set - Ελληνικά.mp3","DJ Set - Ellinika.mp3"),
        ("English Song.mp3","Unchanged")
    ]
    for i,(before,after) in enumerate(rows):
        c.setFillColor(DARK);c.setFont("DV",8.5)
        c.drawString(L+12,y-55-i*32,before)
        c.drawString(L+230,y-55-i*32,after)
    y-=209;y=heading(c,"Built-in safeguards",y)
    for item in [
        "Preview and confirmation: nothing changes until you type YES.",
        "Existing Latin-only names are never overwritten.",
        "Conflicting names get a suffix such as (2), (3), etc.",
        "Subfolder processing is optional; symlinks and junctions are skipped.",
        "Completed renames are recorded in a CSV undo log."
    ]:
        y=paragraph(c,"•  "+item,y,size=9,leading=15)-8
    y-=8;box(c,y,109)
    c.setFillColor(TEAL);c.setFont("DVB",9.5)
    c.drawString(L+14,y-23,"ABOUT TRANSLITERATION")
    paragraph(c,"Rules are inspired by ELOT 743 / ISO 843. Accents are removed and some spellings are simplified. This is not an exact or certified implementation.",y-38,width=435,size=8.7,leading=15)
    c.showPage()
    # Page 4: restoring names and help
    base(c,4);y=section(c,"03 / RECOVERY","Undo and troubleshooting")
    y=paragraph(c,"After renaming, the selected directory contains a CSV log named greeklish_rename_log_*.csv. Keep it to restore original names.",y)-18
    y=heading(c,"Undo changes",y)
    y=paragraph(c,"In PowerShell inside the script folder, run:",y+2)-12
    c.setFillColor(NAVY);c.roundRect(L,y-88,R-L,88,9,fill=1,stroke=0)
    paragraph(c,'<font color="#FFFFFF">py rename_greek_to_greeklish.py `</font><br/><font color="#FFFFFF">--path &quot;D:\\Music&quot; --undo &quot;D:\\Music\\greeklish_rename_log_...csv&quot;</font>',y-15,width=R-L-30,size=8.2,leading=22,x=L+15)
    y-=113
    y=paragraph(c,"Type UNDO to confirm. Missing files and occupied original names are skipped, not overwritten. Undo is best before further moves or manual renames.",y)-20
    y=heading(c,"Useful command-line options",y)
    for flag,meaning in [
        ("--dry-run","Preview without changes."),
        ("--recursive","Include subdirectories."),
        ("--no-recursive","Scan selected folder only."),
        ("--files-only","Keep folder names unchanged.")
    ]:
        y=paragraph(c,f"<b>{flag}</b> — {meaning}",y,size=9)-5
    y-=9;y=heading(c,"Troubleshooting",y)
    for title,desc in [
        ("Python not found","Install Python 3.10+ and check py or python works."),
        ("Nothing to rename","Check the selected folder and subdirectory option."),
        ("Access denied","Close programs using files and check folder permissions.")
    ]:
        y=paragraph(c,f"<b>{title}:</b> {desc}",y,size=8.7,leading=15)-6
    y-=8;box(c,y,59)
    paragraph(c,"<b>Author:</b> Dimitris Laidis<br/><b>Support:</b> github.com/DimitrisLai/Greek-to-greeklish-renamer",y-10,width=445,size=8.5,leading=18)
    c.showPage()
    c.save()

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    build(args.output)
    print(args.output)

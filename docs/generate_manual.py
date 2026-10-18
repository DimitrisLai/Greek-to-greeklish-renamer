"""Public user manual — Greek to Greeklish Renamer v1.2.1.

Build-time requirement: reportlab, DejaVu and Lato fonts. No runtime dependency.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

W,H=A4; M=61; RIGHT=W-M; WIDTH=W-2*M
NAVY=HexColor('#0C192C'); NAVY2=HexColor('#142A43')
TEAL=HexColor('#009D97'); WHITE=HexColor('#FFFFFF')
INK=HexColor('#152437'); MID=HexColor('#516173')
PALE=HexColor('#EFF3F6'); PALEBLUE=HexColor('#E9F0FA')
LINE=HexColor('#DDE3E9')
REG='Lato'; BOLD='LatoBold'; HEAVY='LatoHeavy'; MONO='DejaVuMono'


def init_fonts():
    lato=Path('/usr/share/fonts/truetype/lato'); dej=Path('/usr/share/fonts/truetype/dejavu')
    pdfmetrics.registerFont(TTFont(REG,str(lato/'Lato-Regular.ttf')))
    pdfmetrics.registerFont(TTFont(BOLD,str(lato/'Lato-Bold.ttf')))
    pdfmetrics.registerFont(TTFont(HEAVY,str(lato/'Lato-Heavy.ttf')))
    pdfmetrics.registerFont(TTFont(MONO,str(dej/'DejaVuSansMono.ttf')))
    pdfmetrics.registerFontFamily(REG,normal=REG,bold=BOLD)


def para(c,html,y,x=M,width=WIDTH,size=10.1,leading=15.8,color=INK):
    s=ParagraphStyle('para',fontName=REG,fontSize=size,leading=leading,textColor=color)
    item=Paragraph(html,s)
    _,h=item.wrap(width,900)
    item.drawOn(c,x,y-h)
    return y-h


def section(c,title,y):
    c.setFillColor(INK);c.setFont(BOLD,12.1);c.drawString(M,y,title)
    return y-20


def body_page(c,n,title,deck):
    c.setFillColor(WHITE);c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(NAVY);c.rect(0,H-58,W,58,fill=1,stroke=0)
    c.setFont(BOLD,8);c.setFillColor(WHITE);c.drawString(M,H-35,'GREEK TO GREEKLISH RENAMER')
    c.setFont(REG,8);c.setFillColor(HexColor('#B6C5D5'));c.drawRightString(RIGHT,H-35,'USER MANUAL  /  v1.2.1')
    c.setFont(HEAVY,22.0);c.setFillColor(NAVY);c.drawString(M,H-111,title)
    y=para(c,deck,H-129,size=10,leading=15.5,color=MID)-20
    c.setStrokeColor(LINE);c.line(M,53,RIGHT,53)
    c.setFont(REG,7.7);c.setFillColor(MID)
    c.drawString(M,37,'Dimitris Laidis  /  Greek-to-greeklish-renamer  /  MIT License')
    c.drawRightString(RIGHT,37,f'{n:02d}')
    return y


def table(c,headers,rows,y,widths,heights=None):
    if heights is None: heights=[40]*len(rows)
    c.setFillColor(NAVY);c.rect(M,y-32,WIDTH,32,fill=1,stroke=0)
    x=M
    for h,w in zip(headers,widths):
        c.setFont(BOLD,8.5);c.setFillColor(WHITE);c.drawString(x+12,y-21,h);x+=w
    y-=32
    for idx,(vals,rh) in enumerate(zip(rows,heights)):
        c.setFillColor(PALE if idx%2 else WHITE);c.rect(M,y-rh,WIDTH,rh,fill=1,stroke=0)
        xx=M
        for val,w in zip(vals,widths):
            para(c,str(val),y-9,xx+12,w-20,size=9.25,leading=13.4)
            xx+=w
        y-=rh
    return y-20


def note(c,title,body,y,color=PALEBLUE,height=87):
    c.setFillColor(color);c.rect(M,y-height,WIDTH,height,fill=1,stroke=0)
    c.setFillColor(TEAL);c.setFont(BOLD,9);c.drawString(M+16,y-24,title.upper())
    para(c,body,y-34,M+16,WIDTH-34,size=9.5,leading=15)
    return y-height-22


def bullet(c,items,y):
    for item in items:
        c.setFillColor(TEAL);c.circle(M+5,y-7,2.3,stroke=0,fill=1)
        y=para(c,item,y,M+19,WIDTH-19,size=9.9,leading=15.8)-12
    return y


def code(c,rows,y,height=None):
    height=height or (23+len(rows)*20)
    c.setFillColor(PALEBLUE);c.rect(M,y-height,WIDTH,height,fill=1,stroke=0)
    c.setFillColor(NAVY);c.setFont(MONO,8.3)
    for i,row in enumerate(rows):
        c.drawString(M+17,y-25-i*20,row)
    return y-height-20


def cover(c):
    c.setFillColor(NAVY);c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(TEAL);c.rect(0,H-15,W,15,fill=1,stroke=0)
    # The abstract circles are subtle editorial shapes, not Greek/ethnic artwork.
    c.setFillColor(NAVY2);c.circle(W+73,H-148,210,stroke=0,fill=1)
    c.setFillColor(HexColor('#123E43'));c.circle(W+86,-85,193,stroke=0,fill=1)
    c.setFont(BOLD,10);c.setFillColor(TEAL)
    c.drawString(M,H-182,'USER MANUAL  /  OCTOBER 2026')
    c.setFillColor(WHITE);c.setFont(HEAVY,40)
    c.drawString(M,H-249,'Greek to')
    c.drawString(M,H-298,'Greeklish')
    c.drawString(M,H-347,'Renamer')
    c.setFont(REG,14);c.setFillColor(HexColor('#CAD5E0'))
    c.drawString(M,H-394,'Rename Greek filenames and folders.')
    c.drawString(M,H-417,'Preview first. Confirm every change.')
    c.setStrokeColor(HexColor('#284458'));c.line(M,185,RIGHT,185)
    c.setFont(REG,9.6);c.setFillColor(HexColor('#AFC0D2'))
    c.drawString(M,160,'Folder selection  /  Optional subfolders  /  CSV undo log')
    c.setFont(BOLD,10);c.setFillColor(TEAL)
    c.drawString(M,108,'v1.2.1  /  OPEN SOURCE  /  PYTHON 3.10+')
    c.setFont(REG,9.2);c.setFillColor(HexColor('#AFC0D2'))
    c.drawString(M,79,'Created by Dimitris Laidis')
    c.drawString(M,58,'github.com/DimitrisLai/Greek-to-greeklish-renamer')
    c.showPage()


def p2(c):
    y=body_page(c,2,'01 / Get started','Greek to Greeklish Renamer converts Greek letters in filenames and folder names into Latin characters. It works on the names of items, not their contents.')
    y=section(c,'Requirements',y)
    y=bullet(c,['Windows 10/11 for the double-click launcher; Python <b>3.10 or newer</b> installed.',
                'No extra Python packages or internet connection needed to run the renamer.',
                'Rename permission for the chosen folder; keep a separate backup for important data.'],y)-7
    y=section(c,'Five easy steps',y)
    y=bullet(c,['Download and <b>extract</b> the Windows ZIP from GitHub Releases.',
                'Double-click <b>Run_Greek_to_Greeklish.cmd</b>.',
                'Paste a directory path, or press Enter to use the folder containing the script.',
                'Answer <b>Y</b> to include subfolders, or <b>N / Enter</b> to scan the selected folder only.',
                'Review the proposal. Type the exact word <b>YES</b> to apply or cancel otherwise.'],y)-2
    y=section(c,'What is in the Windows ZIP?',y)
    y=table(c,['FILE','PURPOSE'],[
        ('rename_greek_to_greeklish.py','Main renaming program.'),
        ('Run_Greek_to_Greeklish.cmd','Windows launcher; double-click to run.'),
        ('User Manual / LICENSE / AUTHOR.txt','Instructions, license terms and author credit.')
    ],y,[243,WIDTH-243],[44,44,49])
    note(c,'Important','Do not run the launcher directly inside the ZIP preview. Extract the files first.',y,height=74)
    c.showPage()


def p3(c):
    y=body_page(c,3,'02 / Your first rename','Choose a folder and review the preview before changing any names. The Windows launcher keeps the console open when the program ends.')
    y=section(c,'Example interactive session',y)
    y=code(c,['GREEK TO GREEKLISH RENAMER v1.2.1','Folder path: D:\\Music','Include subdirectories? [y/N]: n','','  Ελληνικά.mp3  -->  Ellinika.mp3','  Μουσική.flac  -->  Mousiki.flac','','Proposed changes: 2','Type YES to apply changes:'],y,219)
    y=section(c,'Confirmation rules',y)
    y=bullet(c,['The program does not rename anything before the confirmation prompt.',
                '<b>YES</b> (uppercase) approves the proposed rename operations.',
                'Press Enter or type anything else to cancel without renaming.',
                'For large folders, the on-screen preview displays up to <b>80</b> planned changes, plus a count of the rest.'],y)
    note(c,'After running','The program reports the number renamed and writes a dated <b>greeklish_rename_log_*.csv</b> file in the selected folder. Keep the CSV for undo.',y,height=90)
    c.showPage()


def p4(c):
    y=body_page(c,4,'03 / Subfolders and scope','The program asks whether you want to include subdirectories. Each choice has a different effect on the scan.')
    y=table(c,['ANSWER','WHAT HAPPENS'],[
       ('N or Enter','Only files directly inside the selected directory are examined; subfolders stay untouched.'),
       ('Y','Files in nested folders are included. Greek-named subfolders are renamed after their contents.')
    ],y,[137,WIDTH-137],[66,71])
    y=section(c,'Examples',y)
    y=code(c,['D:\\Music\\Ελληνικά.mp3    -> D:\\Music\\Ellinika.mp3',
              'D:\\Music\\Greek\\Τραγούδι.mp3  -> ...\\Tragoudi.mp3'],y,88)
    y=section(c,'Files only, even with recursive scanning',y)
    y=para(c,'Use <b>--recursive --files-only</b> to inspect files in subfolders while keeping all directory names unchanged.',y)-22
    y=section(c,'Names containing no Greek letters',y)
    y=bullet(c,['<b>English Song.mp3</b> stays exactly as it is.',
                '<b>Artist - Ελληνικό.mp3</b> is eligible because part of its name contains Greek letters.',
                'The application does not inspect lyrics, audio tags, photo contents or document text.'],y)
    note(c,'Link protection','Symbolic links and Windows junctions/reparse points are skipped during traversal.',y,height=76)
    c.showPage()


def p5(c):
    y=body_page(c,5,'04 / Renaming examples','Greeklish spelling is approximate: the tool follows simplified ELOT 743 / ISO 843-inspired ASCII transcription rules.')
    y=table(c,['ORIGINAL FILENAME','PROPOSED RESULT'],[
       ('Γιώργος Μαζωνάκης.mp3','Giorgos Mazonakis.mp3'),
       ('Δημήτρης Κόκοτας.flac','Dimitris Kokotas.flac'),
       ('DJ Set - Ελληνικά.mp3','DJ Set - Ellinika.mp3'),
       ('Αυτοκίνητο.jpg','Aftokinito.jpg'),
       ('English Song.mp3','Unchanged'),
    ],y,[WIDTH*.49,WIDTH*.51],[43]*5)
    y=section(c,'What is preserved?',y)
    y=bullet(c,['Original file contents, file types and existing Latin text.',
                'File extensions such as <b>.mp3</b>, <b>.flac</b>, and <b>.jpg</b>.',
                'Spaces, punctuation and the relative folder structure, except eligible Greek names.'],y)-3
    note(c,'Spelling limitation','The program removes accents and uses simplified context rules. It is <b>not</b> a certified, reversible implementation of ELOT 743. Proper-name spellings may differ.',y,height=95)
    c.showPage()


def p6(c):
    y=body_page(c,6,'05 / Safety and conflicts','The renamer uses a preview-first design, but bulk renaming can affect applications or playlists that reference the original paths.')
    y=section(c,'Safety behavior',y)
    y=bullet(c,['No changes without the exact YES confirmation (unless you intentionally use <b>--yes</b>).',
                'An existing file or folder is never deliberately replaced by the renamer.',
                'When a new Latin filename is already occupied, the tool adds a suffix such as <b>(2)</b> or <b>(3)</b>.',
                'Each successful operation is added to a UTF-8 CSV log, which can later be used for undo.',
                'Linked folders and Windows junctions are excluded.'],y)-4
    y=section(c,'Filename conflict example',y)
    y=table(c,['EXISTING NAMES','RESULT'],[
        ('Ελληνικά.mp3 + Ellinika.mp3','Ellinika.mp3 stays; the Greek file is renamed to Ellinika (2).mp3.')
    ],y,[WIDTH*.46,WIDTH*.54],[82])
    note(c,'Before a large rename','Run <b>--dry-run</b> first, back up important files, and close players, editors or sync programs using the folder.',y,height=83)
    c.showPage()


def p7(c):
    y=body_page(c,7,'06 / Undo and recovery','The program stores original and new relative paths in a dated CSV log after you confirm renaming.')
    y=section(c,'How to restore original filenames',y)
    y=bullet(c,['Keep the original CSV file produced by the renaming run.',
                'Open Command Prompt or PowerShell where the Python script is located.',
                'Provide both the selected folder path and the CSV log path as shown below.',
                'Type <b>UNDO</b> at the confirmation prompt.'],y)
    y=code(c,['py rename_greek_to_greeklish.py --path "D:\\Music"',
              '  --undo "D:\\Music\\greeklish_rename_log_...csv"'],y,84)
    y=section(c,'What undo does and does not do',y)
    y=bullet(c,['Recorded changes are restored in reverse order, allowing renamed parent folders to be restored before their contents.',
                'If an original path is already occupied, that item is skipped rather than overwritten.',
                'Missing files, additional manual moves, and unrelated edits cannot be reliably undone from the CSV.',
                'Undo logs contain filenames/paths; check them before sharing publicly.'],y)
    note(c,'Keep the CSV','Do not delete the log until you have verified the renamed files and no longer need to restore their original names.',y,height=81)
    c.showPage()


def p8(c):
    y=body_page(c,8,'07 / Command-line reference','The supplied Windows launcher handles normal interactive use. Python command-line options support more precise or repeatable runs.')
    y=table(c,['OPTION','EFFECT'],[
       ('--path "FOLDER"','Select a directory without the initial folder prompt.'),
       ('--recursive','Include subdirectories without asking.'),
       ('--no-recursive','Scan the selected folder only.'),
       ('--files-only','Keep folder names unchanged while scanning files.'),
       ('--dry-run','Show proposed changes without renaming anything.'),
       ('--yes','Skip the confirmation prompt; use carefully.'),
       ('--undo "CSV"','Restore from a previous CSV log.'),
       ('--help / --version','Display command help or version information.'),
    ],y,[156,WIDTH-156],[42]*8)
    y=section(c,'Read-only preview',y)
    y=code(c,['py rename_greek_to_greeklish.py --path "D:\\Music"','  --no-recursive --dry-run'],y,82)
    note(c,'Power users','When neither --recursive nor --no-recursive is given, the program asks the subdirectory question even if --path is supplied.',y,height=82)
    c.showPage()


def p9(c):
    y=body_page(c,9,'08 / Troubleshooting','Most issues can be resolved by checking the selected folder, Python availability, file permissions or the preview output.')
    y=table(c,['SYMPTOM','WHAT TO CHECK'],[
       ('Python not found','Install Python 3.10+; try py -3 or python in Command Prompt.'),
       ('Nothing proposed','Check the path, Greek letters in names, and whether subfolders were included.'),
       ('File in use / access denied','Close applications using the files and verify folder permissions.'),
       ('Unexpected (2) suffix','Another item already uses the intended Latin filename.'),
       ('Undo skips an item','Original path is occupied or the renamed file has been moved/missing.'),
       ('Words look unusual','Simplified transliteration differs from some preferred personal spellings.'),
    ],y,[170,WIDTH-170],[49,55,54,49,56,55])
    y=section(c,'Project information',y)
    y=para(c,'<b>Created by Dimitris Laidis</b><br/>Version 1.2.1 · Python 3.10+ · MIT License<br/>github.com/DimitrisLai/Greek-to-greeklish-renamer',y,size=9.8,leading=18)-15
    note(c,'Reporting an issue','Use GitHub Issues and include the version, Python/Windows version, exact message and a small example with invented filenames. Avoid sharing personal paths or full music libraries.',y,height=94)
    c.showPage()


def generate(output):
    init_fonts();output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(output),pagesize=A4,pageCompression=1)
    c.setAuthor('Dimitris Laidis')
    c.setTitle('Greek to Greeklish Renamer - Complete User Manual v1.2.1')
    c.setSubject('Public software manual: usage, controls, safety, undo, and troubleshooting')
    cover(c)
    for fn in (p2,p3,p4,p5,p6,p7,p8,p9):fn(c)
    c.save()
    return output


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();print(generate(args.output))
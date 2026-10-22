#!/usr/bin/env python3
"""Produce the public v2.4.0 user manual (build-time dependency: ReportLab)."""
from __future__ import annotations

import argparse
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

VERSION = '2.4.0'
AUTHOR = 'Dimitris Laidis'
REPO = 'github.com/DimitrisLai/Greek-to-greeklish-renamer'
W, H = A4
L, R = 58, W-58
CW = R-L
NAVY=HexColor('#0B1728'); NAVY2=HexColor('#142B44')
TEAL=HexColor('#009E99'); WHITE=colors.white; INK=HexColor('#142239')
SUB=HexColor('#536578'); PALE=HexColor('#F1F5F8'); CLOUD=HexColor('#E8F0F9')
LINE=HexColor('#DAE3EA'); CYAN=HexColor('#B9E7E4')


def fonts():
    p=Path('/usr/share/fonts/truetype/lato')
    q=Path('/usr/share/fonts/truetype/dejavu')
    pdfmetrics.registerFont(TTFont('Lato',str(p/'Lato-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('LatoB',str(p/'Lato-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('LatoH',str(p/'Lato-Heavy.ttf')))
    pdfmetrics.registerFont(TTFont('Mono',str(q/'DejaVuSansMono.ttf')))
    pdfmetrics.registerFontFamily('Lato',normal='Lato',bold='LatoB')


def paragraph(c,html,y,x=L,width=CW,size=10,leading=16,color=INK,bold=False):
    style=ParagraphStyle('inline',fontName='LatoB' if bold else 'Lato',fontSize=size,
            leading=leading,textColor=color,spaceBefore=0,spaceAfter=0,allowWidows=0,
            allowOrphans=0)
    p=Paragraph(html,style)
    _,height=p.wrap(width,1000)
    p.drawOn(c,x,y-height)
    return y-height


def title(c,n,heading,subtitle):
    c.setFillColor(WHITE);c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(NAVY);c.rect(0,H-53,W,53,fill=1,stroke=0)
    c.setFont('LatoB',8.5);c.setFillColor(WHITE)
    c.drawString(L,H-33,'GREEK TO GREEKLISH RENAMER')
    c.setFont('Lato',8);c.setFillColor(CYAN)
    c.drawRightString(R,H-33,'USER MANUAL   /   v'+VERSION)
    c.setFont('LatoH',23);c.setFillColor(NAVY)
    c.drawString(L,H-111,f'{n:02d} / {heading}')
    y=paragraph(c,subtitle,H-130,size=10.1,leading=16,color=SUB)-25
    c.setStrokeColor(LINE);c.line(L,55,R,55)
    c.setFillColor(SUB);c.setFont('Lato',7.7)
    c.drawString(L,36,f'{AUTHOR}  /  {REPO}  /  MIT License')
    c.drawRightString(R,36,f'{n+1:02d}')
    return y


def section(c,text,y):
    c.setFillColor(NAVY);c.setFont('LatoB',12)
    c.drawString(L,y,text)
    return y-20


def bullets(c,items,y,margin=0):
    for item in items:
        c.setFillColor(TEAL);c.circle(L+6+margin,y-7,2.1,fill=1,stroke=0)
        y=paragraph(c,item,y,L+21+margin,CW-22-margin,size=9.8,leading=15.5)-10
    return y


def table(c,headers,rows,y,widths=None,size=9.4,padding=10):
    if widths is None: widths=[CW/len(headers)]*len(headers)
    assert sum(widths)<=CW+1
    hh=32
    c.setFillColor(NAVY);c.rect(L,y-hh,CW,hh,fill=1,stroke=0)
    xx=L
    for head,ww in zip(headers,widths):
        c.setFont('LatoB',8.4);c.setFillColor(WHITE)
        c.drawString(xx+11,y-21,head)
        xx+=ww
    y-=hh
    for i,row in enumerate(rows):
        cols=[]
        for value,width in zip(row,widths):
            s=ParagraphStyle('cell',fontName='Lato',fontSize=size,leading=size+4,
                             textColor=INK)
            p=Paragraph(str(value),s)
            _,h=p.wrap(width-2*padding,500)
            cols.append((p,h))
        rh=max(30,max(h for p,h in cols)+17)
        c.setFillColor(PALE if i%2 else WHITE)
        c.rect(L,y-rh,CW,rh,fill=1,stroke=0)
        xx=L
        for (p,h),ww in zip(cols,widths):
            p.drawOn(c,xx+padding,y-padding-h)
            xx+=ww
        y-=rh
    return y-23


def code(c,lines,y,size=8.4):
    height=len(lines)*21+26
    c.setFillColor(CLOUD);c.rect(L,y-height,CW,height,fill=1,stroke=0)
    c.setFillColor(NAVY);c.setFont('Mono',size)
    for i,line in enumerate(lines):
        if pdfmetrics.stringWidth(line,'Mono',size)>CW-31:
            raise ValueError('code block line too long: '+line)
        c.drawString(L+16,y-23-21*i,line)
    return y-height-20


def note(c,heading,text,y,height=None):
    s=ParagraphStyle('note',fontName='Lato',fontSize=9.7,leading=15.3,textColor=INK)
    p=Paragraph(text,s);_,h=p.wrap(CW-35,400)
    hh=height or max(74,h+48)
    c.setFillColor(CLOUD);c.rect(L,y-hh,CW,hh,fill=1,stroke=0)
    c.setFillColor(TEAL);c.setFont('LatoB',8.6)
    c.drawString(L+16,y-24,heading.upper())
    p.drawOn(c,L+16,y-34-h)
    return y-hh-20


def check(y,what):
    if y<75:raise AssertionError('Page layout overflow: '+what+' at '+str(y))


def make(out:Path):
    fonts();out.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(out),pagesize=A4,pageCompression=1)
    c.setTitle('Greek to Greeklish Renamer — Complete User Manual v'+VERSION)
    c.setAuthor(AUTHOR)
    c.setSubject('Windows desktop UI, command-line usage, CSV undo and safe filename transliteration')
    c.setKeywords('Greek, Greeklish, ELOT 743, Windows, file renamer, transliteration')
    # Page 1 - editorial cover, matching the user's other manuals
    c.setFillColor(NAVY);c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(TEAL);c.rect(0,H-14,W,14,fill=1,stroke=0)
    c.setFillColor(NAVY2);c.circle(W+48,H-78,188,fill=1,stroke=0)
    c.setFillColor(HexColor('#124849'));c.circle(W-20,-80,175,fill=1,stroke=0)
    c.setFillColor(CYAN);c.setFont('LatoB',11)
    c.drawString(61,H-160,'WINDOWS DESKTOP APPLICATION  /  USER MANUAL')
    c.setFillColor(WHITE);c.setFont('LatoH',37)
    c.drawString(61,H-228,'Greek to')
    c.drawString(61,H-278,'Greeklish Renamer')
    c.setFillColor(HexColor('#CBD9E4'));c.setFont('Lato',14)
    c.drawString(62,H-327,'Rename confidently. Preview every change.')
    c.drawString(62,H-350,'Keep English filenames untouched.')
    c.setStrokeColor(TEAL);c.setLineWidth(3);c.line(62,H-398,228,H-398)
    c.setFillColor(HexColor('#BCD1DE'));c.setFont('Lato',10.2)
    c.drawString(62,H-454,'Remembered settings  /  Cancel scan  /  History')
    c.drawString(62,H-477,'Safe renaming  /  Undo  /  Standalone EXE')
    c.setFont('LatoB',11);c.setFillColor(CYAN)
    c.drawString(62,103,'VERSION 2.4.0  /  OPEN SOURCE  /  MIT LICENSE')
    c.setFillColor(HexColor('#ADBECD'));c.setFont('Lato',10)
    c.drawString(62,78,'Created by Dimitris Laidis')
    c.drawString(62,56,REPO)
    c.showPage()

    # Page 2
    y=title(c,1,'Start here','Choose the correct download, then complete a safe first run in a few minutes.')
    y=section(c,'Which file should I download?',y)
    y=table(c,['DOWNLOAD','WHO IT IS FOR'],[
       ('<b>Windows ZIP (recommended)</b>','Contains the compiled <b>GreeklishRenamer.exe</b>, PDF manual, license and quick-start text. <b>No Python installation.</b>'),
       ('<b>Source ZIP</b>','For developers and Python users: GUI, command-line edition, tests, documentation and build scripts.'),
       ('<b>PDF User Manual</b>','This document; also included in the Windows ZIP.')],y,[179,CW-179],size=9.3)
    y=section(c,'Your first scan in six steps',y)
    y=bullets(c,[
       '<b>1.</b> Download the Windows ZIP from the v2.4.0 GitHub Release.',
       '<b>2.</b> Right-click the ZIP and choose <b>Extract All</b>.',
       '<b>3.</b> Double-click <b>GreeklishRenamer.exe</b>.',
       '<b>4.</b> Browse to a test folder with a few Greek filenames.',
       '<b>5.</b> Choose a file-type filter and click <b>Preview changes</b>. Cancel scan if needed.',
       '<b>6.</b> Find and untick unwanted entries; correct a proposed name; apply only checked rows.'
    ],y)
    y=note(c,'Start safely','Make a separate backup before bulk changes. The preview does not modify files. A CSV undo log is created for each applied run.',y)
    check(y,'start page');c.showPage()

    # Page 3
    y=title(c,2,'Meet the desktop interface','A focused window for selecting a folder, reviewing changes, applying renames and restoring names.')
    y=section(c,'Screen guide',y)
    y=table(c,['AREA','WHAT IT DOES'],[
        ('<b>Folder location</b>','Browse to select a folder; the last existing directory is remembered locally.'),
        ('<b>File-type filter</b>','All, audio, MP3, FLAC, WAV or custom extensions; last choice is remembered.'),
        ('<b>Preview / Cancel scan</b>','Live file/folder counters; cancelling discards the partial scan without renaming.'),
        ('<b>Explorer menu (classic)</b>','Optional per-user right-click preview under Show more options on Windows 11.'),
        ('<b>Select All / Select None toggle</b>','One toggle switches between Select None (all checked) and Select All (otherwise).'),
        ('<b>Edit selected…</b>','Edit a proposed name. File extensions are protected unless you explicitly opt into advanced changes.'),
        ('<b>Find / Show filters</b>','Search original or proposed paths; show All, Included, Excluded or Edited. Selection remains unchanged.'),
        ('<b>Apply / Stop safely</b>','Apply checked names, or request a safe stop between filenames. Window closing is blocked while busy.'),
        ('<b>Results / Undo</b>','Review per-file outcomes and reasons. Keep the separate undo CSV.'),
        ('<b>History…</b>','Browse undo logs saved in the selected folder, inspect their entries and request a confirmed undo.')
    ],y,[196,CW-196],size=8.85)
    y=paragraph(c,'<b>Safety:</b> Saved settings never start a scan automatically; filtered views do not alter selections.',y,size=8.8,leading=13)-9
    check(y,'interface page');c.showPage()

    # Page 4
    y=title(c,3,'The preview-first workflow','The application is designed to make each proposed change visible before committing it.')
    y=section(c,'What you see before renaming',y)
    y=table(c,['TYPE','CURRENT PATH','PROPOSED PATH'],[
       ('File','Ελληνικά.mp3','Ellinika.mp3'),
       ('File','DJ - Ελληνικά.flac','DJ - Ellinika.flac'),
       ('Folder','Μουσική','Mousiki'),
       ('File','Αθήνα/Τραγούδι.mp3','Αθήνα/Tragoudi.mp3')
    ],y,[62,191,CW-253],size=9.1)
    y=section(c,'Choose, correct and apply only what you want',y)
    y=bullets(c,[
       'Each row starts checked; click INCLUDE or press Space to toggle it.',
       'One button toggles <b>Select All / Select None</b> across every row, even those hidden by filters.',
       'Select a row and use <b>Edit selected</b> to correct its name. Extensions are locked unless explicitly unlocked in the advanced option.',
       'Search original/proposed names, or filter Included, Excluded or Edited; hidden rows keep their selections. Apply only checked rows.',
       'If the directory changes after preview, Apply is rejected and a fresh preview is required.',
       'Uncheck a parent folder if you exclude a proposed rename inside it.',
       '<b>Stop safely</b> finishes the current file and saves its undo entry; do not force-close the app.',
       'Results show renamed, skipped, failed, excluded and unprocessed items with reasons.',
    ],y)
    y=note(c,'Do not treat preview as a file-content comparison','This tool modifies filenames and directory names, not media metadata, contents, lyrics or audio. It does not compare hashes or file quality.',y)
    check(y,'preview page');c.showPage()

    # Page 5
    y=title(c,4,'Folders and subdirectories','Control scope independently: scan inside subfolders, and optionally rename the subfolders themselves.')
    y=table(c,['INCLUDE SUBDIRECTORIES','RENAME GREEK FOLDERS','BEHAVIOR'],[
       ('<b>Off (default)</b>','Disabled','Only files directly inside the selected folder are considered.'),
       ('<b>On</b>','Off','Files are considered recursively; folder names remain unchanged.'),
       ('<b>On</b>','On','Files and Greek-named folders are candidates for renaming.')
    ],y,[137,135,CW-272],size=9)
    y=section(c,'Example: an artist collection',y)
    y=code(c,['BEFORE  /  Music / Ελληνικά / Τραγούδι.mp3',
              'AFTER   /  Music / Ellinika / Tragoudi.mp3'],y,size=7.9)
    y=paragraph(c,'With the second option disabled, <b>Ελληνικά</b> remains the same folder name, while <b>Τραγούδι.mp3</b> becomes <b>Tragoudi.mp3</b>.',y,size=9.7)-20
    y=section(c,'Linked directories are excluded',y)
    y=bullets(c,[
       'Recursive scans skip symbolic links and Windows junction / reparse points.',
       'The selected root directory must be a normal accessible folder, not a link.',
       'Folder moves are performed after filenames inside the folder, so the undo log can restore paths in reverse order.'
    ],y)
    check(y,'folder page');c.showPage()

    # Page 6
    y=title(c,5,'Greek-to-Greeklish rules','Simple ASCII transcription inspired by ELOT 743 / ISO 843, with Greek accents removed.')
    y=table(c,['ORIGINAL','RESULT','NOTES'],[
       ('Γιώργος Μαζωνάκης.mp3','Giorgos Mazonakis.mp3','Greek name example'),
       ('Δημήτρης Κόκοτας.flac','Dimitris Kokotas.flac','File extension preserved'),
       ('DJ - Ελληνικά.mp3','DJ - Ellinika.mp3','Mixed Latin / Greek'),
       ('Χρήστος.mp3','Christos.mp3','χ → ch'),
       ('Μπάμπης.mp3','Bampis.mp3','Context-dependent μπ'),
       ('Αυτοκίνητο.mp3','Aftokinito.mp3','Context-dependent αυ'),
       ('English Song.mp3','Unchanged','No Greek letters')
    ],y,[175,170,CW-345],size=8.75)
    y=section(c,'A note about spelling',y)
    y=paragraph(c,'Personal names have more than one accepted Latin spelling. This software aims for consistent filename-friendly ASCII results; it is <b>not a certified, fully reversible or exhaustive ELOT 743 implementation</b>. Review names that matter to you.',y,size=9.8,leading=16)-19
    y=note(c,'Greek-only filter','The application examines each file or folder <b>name</b>, never its content. English or already-Greeklish names are skipped.',y)
    check(y,'conversion page');c.showPage()

    # Page 7
    y=title(c,6,'Safety, conflicts and undo','The GUI protects unrelated names, but important collections should still be backed up.')
    y=section(c,'Collision behavior',y)
    y=table(c,['EXISTING NAME','GREEK ORIGINAL','RESULT'],[
       ('Ellinika.mp3','Ελληνικά.mp3','Ellinika (2).mp3'),
       ('Ellinika (2).mp3','Ελληνικά.mp3','Ellinika (3).mp3 (if needed)')
    ],y,[170,160,CW-330],size=8.75)
    y=section(c,'Restoring names',y)
    y=bullets(c,[
       'Keep the <b>greeklish_rename_log_YYYYMMDD_HHMMSS_microseconds.csv</b> created in the chosen folder.',
       'Click <b>History…</b> to list the recent undo logs in the selected folder and review their entries.',
       'Choose <b>Undo selected run</b> from History or <b>Undo from CSV</b> for an older external log.',
       'The separate <b>greeklish_result_log_*.csv</b> lists success, skipped, failed, excluded and not processed with reasons.',
       'Verify that the folder is correct, then type the exact word <b>UNDO</b>.',
       'Atomic no-overwrite moves prevent accidental replacement if a destination becomes occupied. Undo also refuses occupied original names.',
       'Preview and results CSV exports escape spreadsheet formula-like cells. Undo CSVs retain exact names for reliable restoration.'
    ],y)
    y=note(c,'Undo is not an independent backup','Do not delete your separate backups until you verify the results. A crash, locked file, moved directory, concurrent changes or filesystem error can prevent full restoration.',y)
    check(y,'safety page');c.showPage()

    # Page 8
    y=title(c,7,'Source edition and command line','The original command-line renamer remains available for automation and users who prefer console controls.')
    y=section(c,'Run the Python GUI (source edition)',y)
    y=code(c,['py greeklish_gui.py','py greeklish_gui.py --version','py greeklish_gui.py --self-test'],y,size=8.6)
    y=section(c,'Keep using the command-line edition',y)
    y=code(c,['py rename_greek_to_greeklish.py',
       'py rename_greek_to_greeklish.py --path "D:/Music" --dry-run',
       'py rename_greek_to_greeklish.py --path "D:/Music" --recursive',
       'py rename_greek_to_greeklish.py --path "D:/Music" --recursive --files-only'],y,size=7.6)
    y=section(c,'Undo from PowerShell or Command Prompt',y)
    y=code(c,['py rename_greek_to_greeklish.py --path "D:/Music"',
       '  --undo "D:/Music/greeklish_rename_log_...csv"'],y,size=7.7)
    y=paragraph(c,'The two-line undo example above is conceptual; put it on one command line, or use the GUI. The <b>--yes</b> flag skips the CLI confirmation prompt and should only be used deliberately.',y,size=9.3,leading=15.5)
    check(y,'cli page');c.showPage()

    # Page 9
    y=title(c,8,'Troubleshooting','Quick checks for common problems in the Windows UI and Python source edition.')
    y=table(c,['PROBLEM','WHAT TO DO'],[
       ('The EXE does not open','Extract ZIP first. SmartScreen may prompt for unsigned community applications.'),
       ('Nothing found','Check the selected folder and subdirectory option. Only names containing Greek letters qualify.'),
       ('Apply is disabled','Run Preview and check at least one row; changing options clears the preview.'),
        ('Search hides filenames','Search and status filters hide rows only; their Include state remains unchanged.'),
        ('Scan takes too long','Click Cancel scan; the preview is discarded, no files renamed. Run Preview again when ready.'),
       ('Applying takes long','Use Stop safely to finish the current rename and retain logs.'),
       ('Edited name is rejected','File extensions are protected by default. For a deliberate extension change, enable the advanced checkbox.'),
       ('Unchecked child blocks Apply','Uncheck the selected parent folder too, or explicitly select the child.'),
       ('Folder changed before apply','Run Preview again; the stale plan is intentionally rejected.'),
       ('Access denied / locked file','Close music players, editors or sync clients. Check permissions and try again.'),
       ('Undo restores only some rows','Review the CSV and check for moved/missing files or occupied original names.'),
       ('History is empty','Choose the original target folder. History only shows undo CSVs located directly inside that folder.'),
       ('Source GUI fails to start','Confirm Python 3.10+ includes Tkinter. Use the standalone EXE if Python is not available.')
    ],y,[151,CW-151],size=8.8)
    y=paragraph(c,'<b>Note:</b> Test the standalone EXE on your own Windows desktop before large-batch use.',y,size=8.7,leading=13)-9
    check(y,'troubleshooting page');c.showPage()

    # Page 10
    y=title(c,9,'Project information','Release details, support channels and responsible use.')
    y=table(c,['ITEM','DETAIL'],[
       ('Project','Greek to Greeklish Renamer'),
       ('Release','v2.4.0 — Remembered Settings & Cancel Scan'),
       ('Author','Dimitris Laidis / GitHub: DimitrisLai'),
       ('License','MIT (source code); dependencies keep their respective terms'),
       ('Source runtime','Python 3.10+, standard library (Tkinter)'),
       ('Windows build','Standalone, installer-free EXE packaged using PyInstaller'),
       ('Repository',REPO),
       ('Support','GitHub Issues (use fictional example filenames)')
    ],y,[156,CW-156],size=9.1)
    y=section(c,'New in version 2.4.0',y)
    y=bullets(c,[
       'Last valid folder and file-type choices are saved locally and restored without running a scan.',
       'Cancel a slow Preview scan; cancelled scans do not rename files or create undo logs.',
       'Scan cancellation is separate from Stop safely for a rename already being applied.',
       'Modern Windows 11 top-level context menus require a native signed package; the optional classic menu remains under Show more options.',
       'Existing History/Undo, collision safeguards, CSV protections and extension filters remain available.'
    ],y)
    y=note(c,'Privacy and responsible use','The application operates locally. It does not upload filenames or file data. Keep separate backups, verify previews and avoid posting private folder paths in public issue reports.',y)
    check(y,'project page');c.showPage()
    c.save()
    print(out)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    make(a.output)

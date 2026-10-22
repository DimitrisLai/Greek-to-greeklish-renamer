#!/usr/bin/env python3
"""Greek to Greeklish Renamer 2.1.1 — native Windows desktop UI.

Built with Python's standard-library Tkinter. No Tk calls occur on worker threads.
The existing command-line renamer remains available separately.
"""
from __future__ import annotations

import argparse
import csv
import io
import queue
import sys
import tempfile
import threading
import time
import os
from pathlib import Path

# PyInstaller --windowed sets the standard streams to None on Windows.
# The preserved CLI renamer still uses print() for status and undo; provide
# harmless Unicode streams so the GUI never crashes when there is no console.
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from renamer_service import (InvalidSelectionError, PreviewChangedError, RenamePreview,
                             RenameReport, create_preview, execute_preview,
                             execute_preview_report, restore_log,
                             validate_new_filename, validate_selection)
from rename_greek_to_greeklish import VERSION
from renamer_service import parse_extensions
from explorer_integration import register as register_explorer, unregister as unregister_explorer, executable_for_menu

EXTENSION_PRESETS = {
    'All file types': (),
    'Audio (.mp3, .flac, .wav)': ('.mp3', '.flac', '.wav'),
    'MP3 only': ('.mp3',),
    'FLAC only': ('.flac',),
    'WAV only': ('.wav',),
    'Custom list…': None,
}


NAVY = '#101E32'
NAVY2 = '#19304A'
TEAL = '#078F91'
TEAL_HOVER = '#057A7C'
PAPER = '#F5F8FC'
WHITE = '#FFFFFF'
TEXT = '#1C2D42'
MUTED = '#53687D'
BORDER = '#DCE5EE'
PALE = '#E8F2F5'
AMBER = '#B56D0A'
FONT = 'Segoe UI'


def check_headless_build() -> int:
    """Smoke-test frozen exe without requiring a Windows desktop session."""
    with tempfile.TemporaryDirectory(prefix='greeklish-gui-smoke-') as folder:
        root = Path(folder)
        original = root / 'Ελληνικά.mp3'
        original.write_bytes(b'unchanged media bytes')
        skipped = root / 'Αθήνα.mp3'
        skipped.write_bytes(b'skipped unchanged')
        preview = create_preview(root, recursive=False, rename_folders=False)
        if len(preview.operations) != 2:
            return 11
        destination = root / 'Custom Greeklish.mp3'
        changed, log = execute_preview(preview, selected=((original, destination),))
        if changed != 1 or destination.read_bytes() != b'unchanged media bytes' or skipped.read_bytes() != b'skipped unchanged':
            return 12
        count, total = restore_log(root, log)
        if (count, total) != (1, 1) or original.read_bytes() != b'unchanged media bytes' or not skipped.is_file():
            return 13
    # Headless frozen EXE also tests the new stop/report behavior.
    with tempfile.TemporaryDirectory(prefix='greeklish-gui-stop-test-') as folder:
        root = Path(folder)
        for number in range(12):
            (root / f'Αρχείο {number:02d}.mp3').write_bytes(bytes([number]))
        preview = create_preview(root, recursive=False, rename_folders=False)
        stop = threading.Event()
        def advance(done, total, renamed):
            if done == 4:
                stop.set()
        result = execute_preview_report(preview, preview.operations,
                          stop_requested=stop.is_set, progress_callback=advance)
        if (result.renamed_count, result.remaining_count, result.stopped) != (4, 8, True):
            return 14
        if result.report_file is None or not result.report_file.is_file():
            return 15
        if restore_log(root, result.log) != (4,4):
            return 16
    # Frozen Windows build must preserve the extension-filter safety contract.
    with tempfile.TemporaryDirectory(prefix='greeklish-gui-filter-test-') as folder:
        root = Path(folder)
        audio = root / 'Τραγούδι.mp3'
        unrelated = root / 'Σημειώσεις.txt'
        audio.write_bytes(b'mp3 content')
        unrelated.write_bytes(b'text content')
        preview = create_preview(root, recursive=False, rename_folders=False,
                                 file_extensions=('.mp3',))
        if len(preview.operations) != 1:
            return 17
        outcome = execute_preview_report(preview, preview.operations)
        if (outcome.renamed_count != 1 or not unrelated.exists()
            or unrelated.read_bytes() != b'text content'):
            return 18
        if restore_log(root, outcome.log) != (1, 1) or audio.read_bytes() != b'mp3 content':
            return 19
    return 0


class EditNameDialog(simpledialog.Dialog):
    """A text editor with file extension protection enabled by default."""
    def __init__(self, parent, source: Path, proposed: str, override=False):
        self.source = source
        self.proposed = proposed
        self.existing_override = override
        self.result = None
        super().__init__(parent, title='Edit proposed name')

    def body(self, master):
        ttk.Label(master, text=f'Original: {self.source.name}', wraplength=480).pack(anchor='w', pady=(4, 12))
        ttk.Label(master, text='Proposed filename / folder name:').pack(anchor='w')
        self.name_var = tk.StringVar(value=self.proposed)
        self.name_entry = ttk.Entry(master, textvariable=self.name_var, width=57)
        self.name_entry.pack(fill='x', pady=(4, 8))
        self.allow_var = tk.BooleanVar(value=self.existing_override)
        if self.source.is_file():
            self.advanced = ttk.Checkbutton(master,
                text='Allow file extension change (advanced)', variable=self.allow_var)
            self.advanced.pack(anchor='w')
            ttk.Label(master, text=f'Protected extension: {self.source.suffix or "(none)"}. '
                       'Keep the extension unchanged unless explicitly enabled.',
                       foreground=MUTED, wraplength=480).pack(anchor='w', pady=(8, 4))
        else:
            self.allow_var.set(True)
            ttk.Label(master, text='Folder names can include periods.',
                      foreground=MUTED).pack(anchor='w', pady=(6, 4))
        return self.name_entry

    def validate(self):
        try:
            validate_new_filename(self.name_var.get(), original=self.source.name,
                                  allow_extension_change=self.allow_var.get())
            return True
        except InvalidSelectionError as exc:
            messagebox.showerror('Invalid name', str(exc), parent=self)
            return False

    def apply(self):
        self.result = self.name_var.get(), self.allow_var.get()


class ResultsDialog(tk.Toplevel):
    """Read-only per-item results, automatically saved beside the undo log."""
    def __init__(self, parent, report: RenameReport):
        super().__init__(parent)
        self.report = report
        self.title('Rename results — Greek to Greeklish Renamer')
        self.geometry('940x520')
        self.minsize(710, 380)
        self.configure(bg=PAPER)
        self.transient(parent)
        main = tk.Frame(self, bg=PAPER, padx=18, pady=15)
        main.pack(fill='both', expand=True)
        heading = ('Stopped safely' if report.stopped else
                   'Completed with issues' if report.failed_count or report.skipped_count else 'Completed')
        tk.Label(main, text=heading, font=(FONT, 15, 'bold'), bg=PAPER, fg=NAVY).pack(anchor='w')
        summary = (f'{report.renamed_count:,} renamed   •   {report.skipped_count:,} skipped   •   '
                   f'{report.failed_count:,} failed   •   {report.excluded_count:,} excluded   •   '
                   f'{report.remaining_count:,} not processed')
        tk.Label(main, text=summary, font=(FONT, 10), bg=PAPER, fg=TEXT).pack(anchor='w', pady=(8, 12))
        wrap = tk.Frame(main, bg=WHITE)
        wrap.pack(fill='both', expand=True)
        tree = ttk.Treeview(wrap, show='headings', columns=('status','old','new','reason'),
                            style='Greek.Treeview')
        for key, title, width in [('status','RESULT',110), ('old','ORIGINAL',240),
                                  ('new','DESTINATION',240),('reason','DETAIL / REASON',280)]:
            tree.heading(key, text=title)
            tree.column(key, width=width, minwidth=85, stretch=key!='status')
        tree.pack(side='left', fill='both', expand=True)
        sb = ttk.Scrollbar(wrap, orient='vertical', command=tree.yview)
        sb.pack(side='right', fill='y')
        tree.configure(yscrollcommand=sb.set)
        for row in report.rows:
            tree.insert('', 'end', values=(row.status.upper(),
                      str(row.old.relative_to(report.root)),
                      str(row.new.relative_to(report.root)),row.reason))
        tk.Label(main, bg=PAPER, fg=MUTED, anchor='w',
                 text=f'Undo log: {report.log}').pack(anchor='w', pady=(10, 1))
        tk.Label(main, bg=PAPER, fg=MUTED, anchor='w',
                 text=f'Results CSV: {report.report_file or "Could not automatically save (use Export)"}').pack(anchor='w')
        buttons = tk.Frame(main, bg=PAPER)
        buttons.pack(fill='x', pady=(10, 0))
        tk.Button(buttons, text='Export report CSV…', command=self.export,
                  font=(FONT, 10, 'bold'), padx=12, pady=8).pack(side='left')
        tk.Button(buttons, text='Close', command=self.destroy,
                  font=(FONT, 10, 'bold'), padx=12, pady=8).pack(side='right')
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.grab_set()

    def export(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension='.csv',
                  initialfile='greeklish_result_report.csv', filetypes=[('CSV files','*.csv')])
        if path:
            try:
                self.report.export_csv(Path(path))
            except OSError as exc:
                messagebox.showerror('Export failed', str(exc), parent=self)


class GreeklishWindow:
    def __init__(self, root: tk.Tk, initial_folder: Path | None = None):
        self.root = root
        self.root.title(f'Greek to Greeklish Renamer  |  {VERSION}')
        self.root.geometry('1175x800')
        self.root.minsize(920, 625)
        self.root.configure(background=PAPER)
        try:
            self.root.tk.call('tk', 'scaling', 1.2)
        except tk.TclError:
            pass

        self.folder = tk.StringVar(value=str(initial_folder or Path.home()))
        self.recursive = tk.BooleanVar(value=False)
        self.rename_folders = tk.BooleanVar(value=False)
        self.extension_preset = tk.StringVar(value='All file types')
        self.custom_file_types = tk.StringVar(value='.mp3, .flac')
        self.scanning_counter = (0, 0)
        self.scan_last_update = 0.0
        self.filter_text = tk.StringVar()
        self.view_filter = tk.StringVar(value='All')
        self.summary = tk.StringVar(value='Select a folder and click Preview changes.')
        self.counter = tk.StringVar(value='0 proposed changes')
        self.state = tk.StringVar(value='READY')
        self.progress = tk.StringVar(value='No files have been modified.')
        self.apply_meter = tk.DoubleVar(value=0)
        self.apply_meter_label = tk.StringVar(value='')
        self.current_preview: RenamePreview | None = None
        self.checked: dict[int, bool] = {}
        self.manual_targets: dict[int, Path] = {}
        self.extension_overrides: set[int] = set()
        self.stop_event = threading.Event()
        self.current_operation = None
        self.last_log: Path | None = None
        self.processing = False
        self.messages: queue.Queue = queue.Queue()
        self._configure_style()
        try:
            icon_file = (Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
                         / 'assets' / 'GreeklishRenamer.png')
            self.app_icon = tk.PhotoImage(master=root, file=str(icon_file))
            root.iconphoto(True, self.app_icon)
        except (tk.TclError, OSError):
            pass  # The executable's Windows file icon is embedded independently.
        self.checkbox_yes = self._checkbox_icon(True)
        self.checkbox_no = self._checkbox_icon(False)
        self._layout()
        self._bind_events()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self.root.after(80, self._drain_messages)

    def _configure_style(self):
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')
        self.style.configure('Greek.Treeview', background=WHITE, fieldbackground=WHITE,
                             foreground=TEXT, rowheight=31, font=(FONT, 10), borderwidth=0)
        self.style.configure('Greek.Treeview.Heading', background=NAVY2, foreground=WHITE,
                             font=(FONT, 10, 'bold'), borderwidth=0, padding=(12, 11))
        self.style.map('Greek.Treeview', background=[('selected', '#CCE9E9')],
                       foreground=[('selected', NAVY)])
        self.style.configure('Greek.TCheckbutton', background=PAPER, foreground=TEXT,
                             font=(FONT, 10), padding=2)
        self.style.map('Greek.TCheckbutton', background=[('active', PAPER)])
        self.style.configure('Greek.Horizontal.TProgressbar', troughcolor=BORDER,
                             background=TEAL, bordercolor=BORDER, thickness=5)

    def _checkbox_icon(self, enabled: bool) -> tk.PhotoImage:
        """Draw a genuine checkbox graphic; Unicode checkbox glyphs vary by font."""
        icon = tk.PhotoImage(master=self.root, width=20, height=20)
        background = WHITE
        border = TEAL if enabled else '#8798A7'
        icon.put(background, to=(0, 0, 20, 20))
        icon.put(border, to=(2, 2, 18, 18))
        icon.put(TEAL if enabled else WHITE, to=(4, 4, 16, 16))
        if enabled:
            # Thick rasterized white check mark inside the filled square.
            for x, y in [(6, 10), (7, 11), (8, 12), (9, 13),
                         (10, 12), (11, 11), (12, 10), (13, 9), (14, 8)]:
                icon.put(WHITE, to=(x, y, x + 2, y + 2))
        return icon

    def _button(self, parent, label, callback, *, main=False, width=14):
        bg = TEAL if main else WHITE
        fg = WHITE if main else NAVY
        active = TEAL_HOVER if main else PALE
        button = tk.Button(parent, text=label, command=callback, font=(FONT, 10, 'bold'),
                           width=width, bg=bg, fg=fg, activebackground=active,
                           activeforeground=fg, relief='flat', borderwidth=0,
                           padx=13, pady=10, highlightthickness=1,
                           highlightbackground=TEAL if main else BORDER,
                           cursor='hand2')
        return button

    def _layout(self):
        top = tk.Frame(self.root, bg=NAVY, height=104)
        top.pack(fill='x'); top.pack_propagate(False)
        tk.Label(top, text='GREEK TO GREEKLISH', bg=NAVY, fg=WHITE,
                 font=(FONT, 22, 'bold')).place(x=31, y=22)
        tk.Label(top, text='RENAME FILES & FOLDERS  /  PREVIEW FIRST, ALWAYS', bg=NAVY,
                 fg='#A8C5D6', font=(FONT, 9)).place(x=34, y=65)
        tk.Label(top, text=f'v{VERSION}   •   BY DIMITRIS LAIDIS', bg=NAVY,
                 fg='#82CED0', font=(FONT, 9, 'bold')).place(relx=0.98, y=34, anchor='e')

        frame = tk.Frame(self.root, bg=PAPER, padx=28, pady=19)
        frame.pack(fill='both', expand=True)
        tk.Label(frame, text='1   SELECT TARGET FOLDER', bg=PAPER, fg=NAVY,
                 font=(FONT, 10, 'bold')).pack(anchor='w', pady=(0, 8))
        folderrow = tk.Frame(frame, bg=PAPER)
        folderrow.pack(fill='x')
        entry = tk.Entry(folderrow, textvariable=self.folder, relief='flat',
                         font=(FONT, 11), bg=WHITE, fg=TEXT, insertbackground=NAVY,
                         highlightbackground=BORDER, highlightcolor=TEAL,
                         highlightthickness=1)
        entry.pack(side='left', fill='x', expand=True, ipady=9)
        self.folder_entry = entry
        self.browse_btn = self._button(folderrow, 'Browse…', self._browse, width=10)
        self.browse_btn.pack(side='left', padx=(10, 0))

        controls = tk.Frame(frame, bg=PAPER)
        controls.pack(fill='x', pady=(12, 20))
        self.rec_check = ttk.Checkbutton(controls, text='Include subdirectories',
                                         variable=self.recursive, style='Greek.TCheckbutton')
        self.rec_check.pack(side='left')
        self.folder_check = ttk.Checkbutton(controls, text='Also rename Greek folder names',
                                            variable=self.rename_folders,
                                            style='Greek.TCheckbutton')
        self.folder_check.pack(side='left', padx=(28, 0))
        self.explorer_btn = self._button(controls, 'Explorer menu…', self._explorer_menu, width=15)
        self.explorer_btn.pack(side='right')

        type_row = tk.Frame(frame, bg=PAPER)
        type_row.pack(fill='x', pady=(0, 12))
        tk.Label(type_row, text='FILE TYPES:', bg=PAPER, fg=NAVY,
                 font=(FONT, 9, 'bold')).pack(side='left', padx=(0, 12))
        self.type_combo = ttk.Combobox(type_row, textvariable=self.extension_preset,
              values=tuple(EXTENSION_PRESETS), state='readonly', width=27)
        self.type_combo.pack(side='left')
        tk.Label(type_row, text='Custom:', bg=PAPER, fg=MUTED, font=(FONT, 9)).pack(side='left', padx=(13, 5))
        self.custom_type_entry = ttk.Entry(type_row, textvariable=self.custom_file_types, width=29)
        self.custom_type_entry.pack(side='left')
        self.file_type_note = tk.Label(type_row, text='All Greek filenames are eligible',
                 bg=PAPER, fg=MUTED, font=(FONT, 9))
        self.file_type_note.pack(side='right')

        heading = tk.Frame(frame, bg=PAPER)
        heading.pack(fill='x', pady=(0, 9))
        tk.Label(heading, text='2   REVIEW PROPOSED CHANGES', bg=PAPER, fg=NAVY,
                 font=(FONT, 10, 'bold')).pack(side='left')
        tk.Label(heading, textvariable=self.counter, bg=PAPER, fg=TEAL,
                 font=(FONT, 10, 'bold')).pack(side='right')
        self.toggle_btn = self._button(heading, 'Select None', self._toggle_all, width=13)
        self.toggle_btn.pack(side='right', padx=(0, 12))

        searchrow = tk.Frame(frame, bg=PAPER)
        searchrow.pack(fill='x', pady=(0, 10))
        tk.Label(searchrow, text='Find:', bg=PAPER, fg=NAVY,
                 font=(FONT, 9, 'bold')).pack(side='left', padx=(0, 7))
        self.search_entry = ttk.Entry(searchrow, textvariable=self.filter_text, width=38)
        self.search_entry.pack(side='left', fill='x', expand=True)
        tk.Label(searchrow, text='Show:', bg=PAPER, fg=NAVY,
                 font=(FONT, 9, 'bold')).pack(side='left', padx=(14, 8))
        self.filter_combo = ttk.Combobox(searchrow, textvariable=self.view_filter,
              values=('All', 'Included', 'Excluded', 'Edited'), state='readonly', width=12)
        self.filter_combo.pack(side='left')
        tk.Label(searchrow, text='Filtering does not change selections', bg=PAPER,
                 fg=MUTED, font=(FONT, 8)).pack(side='left', padx=(12, 0))

        tablewrap = tk.Frame(frame, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
        tablewrap.pack(fill='both', expand=True)
        tablewrap.grid_rowconfigure(0, weight=1)
        tablewrap.grid_columnconfigure(0, weight=1)
        # The native Treeview #0 column supports a per-row checkbox image.
        # Unlike a text glyph, this stays visible with Windows system fonts.
        self.tree = ttk.Treeview(tablewrap, style='Greek.Treeview', show='tree headings',
                                 columns=('kind', 'before', 'after'))
        self.tree.heading('#0', text='INCLUDE')
        self.tree.column('#0', width=100, minwidth=94, stretch=False, anchor='w')
        self.tree.heading('kind', text='TYPE')
        self.tree.heading('before', text='CURRENT PATH')
        self.tree.heading('after', text='PROPOSED PATH')
        self.tree.column('kind', width=88, stretch=False, anchor='w')
        self.tree.column('before', width=390, minwidth=160, stretch=True)
        self.tree.column('after', width=390, minwidth=160, stretch=True)
        self.tree.tag_configure('odd', background='#F0F5F8')
        self.tree.tag_configure('excluded', background='#EDF0F2', foreground='#8695A4')
        self.tree.tag_configure('custom', background='#E4F6F2')
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar = ttk.Scrollbar(tablewrap, orient='vertical', command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)
        xscroll = ttk.Scrollbar(tablewrap, orient='horizontal', command=self.tree.xview)
        xscroll.grid(row=1, column=0, sticky='ew')
        self.tree.configure(xscrollcommand=xscroll.set)

        status = tk.Frame(frame, bg=PAPER)
        status.pack(fill='x', pady=(11, 0))
        self.state_label = tk.Label(status, textvariable=self.state, bg=PAPER, fg=TEAL,
                                    font=(FONT, 9, 'bold'))
        self.state_label.pack(side='left')
        tk.Label(status, textvariable=self.summary, bg=PAPER, fg=MUTED,
                 font=(FONT, 9)).pack(side='left', padx=14)

        meter_row = tk.Frame(frame, bg=PAPER)
        meter_row.pack(fill='x', pady=(10, 0))
        self.progress_bar = ttk.Progressbar(meter_row, style='Greek.Horizontal.TProgressbar',
                                            maximum=100, variable=self.apply_meter,
                                            mode='determinate')
        self.progress_bar.pack(side='left', fill='x', expand=True, ipady=4)
        tk.Label(meter_row, textvariable=self.apply_meter_label, bg=PAPER, fg=TEAL,
                 font=(FONT, 9, 'bold'), width=34, anchor='e').pack(side='right', padx=(10, 0))

        buttons = tk.Frame(frame, bg=PAPER)
        buttons.pack(fill='x', pady=(10, 0))
        self.preview_btn = self._button(buttons, 'Preview changes', self._preview, main=True, width=17)
        self.preview_btn.pack(side='left')
        self.edit_btn = self._button(buttons, 'Edit selected…', self._edit_selected, width=14)
        self.edit_btn.pack(side='left', padx=(9, 0))
        self.apply_btn = self._button(buttons, 'Apply renames', self._apply, width=14)
        self.apply_btn.pack(side='left', padx=(9, 0))
        self.export_btn = self._button(buttons, 'Export preview', self._export, width=16)
        self.export_btn.pack(side='left', padx=(9, 0))
        self.undo_btn = self._button(buttons, 'Undo from CSV', self._undo, width=14)
        self.undo_btn.pack(side='right')
        self.stop_btn = self._button(buttons, 'Stop safely', self._request_stop, width=13)
        self.stop_btn.pack(side='right', padx=(0, 9))

        footer = tk.Frame(self.root, bg='#E9F0F6', height=45)
        footer.pack(fill='x', side='bottom'); footer.pack_propagate(False)
        tk.Label(footer, textvariable=self.progress, bg='#E9F0F6', fg=MUTED,
                 font=(FONT, 9), anchor='w').pack(side='left', padx=28, fill='x', expand=True)
        tk.Label(footer, text='LOCAL ONLY  •  NO FILE CONTENT CHANGES', bg='#E9F0F6',
                 fg=TEAL, font=(FONT, 8, 'bold')).pack(side='right', padx=26)
        self._sync_controls()

    def _bind_events(self):
        self.folder.trace_add('write', lambda *_: self._invalidate())
        self.recursive.trace_add('write', lambda *_: self._change_recursion())
        self.tree.bind('<ButtonRelease-1>', self._row_click)
        self.tree.bind('<Double-1>', self._row_double_click)
        self.tree.bind('<space>', self._keyboard_toggle)
        self.tree.bind('<<TreeviewSelect>>', lambda *_: self._sync_controls())
        self.rename_folders.trace_add('write', lambda *_: self._invalidate())
        self.extension_preset.trace_add('write', lambda *_: self._file_type_changed())
        self.custom_file_types.trace_add('write', lambda *_: self._custom_type_changed())
        self.filter_text.trace_add('write', lambda *_: self._render_filtered_rows())
        self.view_filter.trace_add('write', lambda *_: self._render_filtered_rows())

    def _change_recursion(self):
        if not self.recursive.get() and self.rename_folders.get():
            self.rename_folders.set(False)
        self._invalidate()

    def _selected_extensions(self):
        preset = self.extension_preset.get()
        if preset == 'Custom list…':
            return parse_extensions(self.custom_file_types.get())
        return EXTENSION_PRESETS[preset]

    def _file_type_changed(self):
        if self.extension_preset.get() != 'All file types' and self.rename_folders.get():
            self.rename_folders.set(False)
        self._invalidate()

    def _custom_type_changed(self):
        if self.extension_preset.get() == 'Custom list…':
            self._invalidate()

    def _invalidate(self):
        self.current_preview = None
        self.checked.clear()
        self.manual_targets.clear()
        self.extension_overrides.clear()
        self.tree.delete(*self.tree.get_children())
        self.counter.set('0 proposed changes')
        if not self.processing:
            self.summary.set('Options changed. Run Preview before applying.')
            self.state.set('READY')
        self._sync_controls()

    def _sync_controls(self):
        state = 'disabled' if self.processing else 'normal'
        for btn in (self.browse_btn, self.preview_btn, self.undo_btn):
            btn.configure(state=state)
        allow_folders = self.recursive.get() and self.extension_preset.get() == 'All file types'
        self.folder_check.configure(state='normal' if allow_folders and not self.processing else 'disabled')
        self.type_combo.configure(state='readonly' if not self.processing else 'disabled')
        self.custom_type_entry.configure(state='normal' if not self.processing and self.extension_preset.get() == 'Custom list…' else 'disabled')
        self.explorer_btn.configure(state='normal' if not self.processing and os.name == 'nt' else 'disabled')
        self.file_type_note.configure(text='Folder renaming disabled with filters' if self.extension_preset.get() != 'All file types' else 'All Greek filenames are eligible')
        self.rec_check.configure(state=state)
        self.folder_entry.configure(state=state)
        has_preview = bool(self.current_preview and self.current_preview.count and not self.processing)
        may_apply = has_preview and any(self.checked.values())
        self.apply_btn.configure(state='normal' if may_apply else 'disabled')
        self.export_btn.configure(state='normal' if has_preview else 'disabled')
        self.edit_btn.configure(state='normal' if has_preview and self.tree.selection() else 'disabled')
        self.toggle_btn.configure(state='normal' if has_preview else 'disabled')
        self.toggle_btn.configure(text='Select None' if has_preview and all(self.checked.values())
                                  else 'Select All')
        self.stop_btn.configure(state='normal' if self.processing and self.current_operation == 'APPLY'
                                and not self.stop_event.is_set() else 'disabled')
        self.search_entry.configure(state='normal' if not self.processing else 'disabled')
        self.filter_combo.configure(state='readonly' if not self.processing else 'disabled')


    def _display_name(self, index: int) -> Path:
        assert self.current_preview is not None
        return self.manual_targets.get(index, self.current_preview.operations[index][1])

    def _selected_operations(self):
        assert self.current_preview is not None
        return tuple((old, self._display_name(i))
                     for i, (old, _automatic) in enumerate(self.current_preview.operations)
                     if self.checked.get(i, False))

    def _refresh_counter(self):
        if self.current_preview is None:
            self.counter.set('0 proposed changes')
            return
        total = self.current_preview.count
        checked = sum(self.checked.values())
        edited = len(self.manual_targets)
        visible = len(self.tree.get_children())
        self.counter.set(f'{checked:,} selected / {total:,} proposed  •  {visible:,} shown' +
                         (f'  |  {edited} edited' if edited else ''))
        self._sync_controls()

    def _set_check(self, index: int, state: bool):
        if self.processing or self.current_preview is None:
            return
        self.checked[index] = state
        self._refresh_row(index)
        self._render_filtered_rows()
        self.summary.set('Only checked rows will be renamed. Unticked rows are skipped.')

    def _refresh_row(self, index: int):
        preview = self.current_preview
        if preview is None:
            return
        old, _ = preview.operations[index]
        new = self._display_name(index)
        tags = (('excluded',) if not self.checked[index] else
                ('custom',) if index in self.manual_targets else
                ('odd',) if index % 2 else ())
        if not self.tree.exists(str(index)):
            return
        self.tree.item(str(index), image=self.checkbox_yes if self.checked[index]
                       else self.checkbox_no, text='Yes' if self.checked[index] else 'No',
                       values=('Folder' if old.is_dir() else 'File',
                               str(old.relative_to(preview.root)),
                               str(new.relative_to(preview.root))), tags=tags)

    def _matching_indices(self) -> list[int]:
        preview = self.current_preview
        if preview is None:
            return []
        search = self.filter_text.get().strip().casefold()
        status = self.view_filter.get()
        result = []
        for i, (old, _) in enumerate(preview.operations):
            if status == 'Included' and not self.checked.get(i, False):
                continue
            if status == 'Excluded' and self.checked.get(i, False):
                continue
            if status == 'Edited' and i not in self.manual_targets:
                continue
            if search and search not in str(old.relative_to(preview.root)).casefold() \
                      and search not in str(self._display_name(i).relative_to(preview.root)).casefold():
                continue
            result.append(i)
        return result

    def _render_filtered_rows(self):
        if self.processing:
            return
        selected_ids = set(self.tree.selection())
        self.tree.delete(*self.tree.get_children())
        for i in self._matching_indices():
            iid = str(i)
            self.tree.insert('', 'end', iid=iid, values=('', '', ''))
            self._refresh_row(i)
            if iid in selected_ids:
                self.tree.selection_add(iid)
        self._refresh_counter()

    def _on_close(self):
        if self.processing:
            if self.current_operation == 'APPLY':
                if messagebox.askyesno('Rename still running',
                         'Renaming is in progress. Close is disabled to protect the undo log.\n\n'
                         'Request a safe stop after the current file?', parent=self.root):
                    self._request_stop()
            else:
                messagebox.showinfo('Please finish the operation',
                     'A scan or restore operation is still running. The window will stay open.',
                     parent=self.root)
            return
        self.root.destroy()

    def _request_stop(self):
        if not self.processing or self.current_operation != 'APPLY':
            return
        self.stop_event.set()
        self.summary.set('Stop requested: finishing the current file and flushing the undo CSV…')
        self._sync_controls()

    def _row_click(self, event):
        if self.processing or self.current_preview is None:
            return
        if self.tree.identify_column(event.x) != '#0':
            return
        row_id = self.tree.identify_row(event.y)
        if row_id and row_id.isdigit():
            i = int(row_id)
            self._set_check(i, not self.checked[i])

    def _row_double_click(self, event):
        if self.processing or self.current_preview is None:
            return
        row_id = self.tree.identify_row(event.y)
        if row_id and self.tree.identify_column(event.x) != '#0':
            self.tree.selection_set(row_id)
            self._edit_selected()

    def _keyboard_toggle(self, event):
        if self.processing or self.current_preview is None:
            return 'break'
        for row_id in self.tree.selection():
            if row_id.isdigit():
                i = int(row_id)
                self._set_check(i, not self.checked[i])
        return 'break'

    def _toggle_all(self):
        if self.current_preview is None or self.processing:
            return
        select_everything = not all(self.checked.values())
        for i in self.checked:
            self.checked[i] = select_everything
            self._refresh_row(i)
        self._render_filtered_rows()
        self.summary.set('All proposed changes selected.' if select_everything else
                         'Nothing selected. Tick individual rows to include them.')

    def _edit_selected(self):
        if self.processing or self.current_preview is None:
            return
        selection = self.tree.selection()
        if not selection:
            return
        i = int(selection[0])
        old, automatic = self.current_preview.operations[i]
        while True:
            editor = EditNameDialog(self.root, old, self._display_name(i).name,
                                    i in self.extension_overrides)
            if editor.result is None:
                return
            value, override = editor.result
            try:
                validate_new_filename(value, original=old.name,
                                      allow_extension_change=override or old.is_dir())
                new = old.with_name(value)
                amended = dict(self.manual_targets)
                overrides = set(self.extension_overrides)
                if new == automatic:
                    amended.pop(i, None)
                    overrides.discard(i)
                else:
                    amended[i] = new
                    if override and old.is_file():
                        overrides.add(i)
                    else:
                        overrides.discard(i)
                if self.checked.get(i, False):
                    proposals = ((source, amended.get(j, target))
                                 for j, (source, target) in enumerate(self.current_preview.operations)
                                 if self.checked.get(j, False))
                    sources_override = {self.current_preview.operations[j][0] for j in overrides}
                    validate_selection(self.current_preview, proposals,
                                       extension_overrides=sources_override)
                self.manual_targets = amended
                self.extension_overrides = overrides
                self._render_filtered_rows()
                self.summary.set(f'Proposed name updated for {old.name}. Review before applying.')
                if self.tree.exists(str(i)):
                    self.tree.see(str(i))
                return
            except (InvalidSelectionError, PreviewChangedError) as exc:
                messagebox.showerror('Invalid filename', str(exc), parent=self.root)

    def _explorer_menu(self):
        """Opt-in HKCU menu; right-click merely selects a folder for preview."""
        if self.processing or os.name != 'nt':
            return
        exe = executable_for_menu()
        question = ('Add a right-click menu for folders and folder backgrounds?\n\n'
                    'YES = install/update the current EXE location\n'
                    'NO = remove both Explorer entries\n'
                    'CANCEL = keep everything unchanged\n\n'
                    'The menu says “Convert to Greeklish (preview)”.\n'
                    'It never applies changes automatically.\n'
                    'Windows 11 may show it under “Show more options”.')
        action = messagebox.askyesnocancel('Explorer right-click integration', question, parent=self.root)
        if action is None:
            return
        try:
            if action:
                if exe is None:
                    messagebox.showinfo('Standalone EXE required',
                        'To install the Explorer menu, launch the downloaded standalone GreeklishRenamer.exe first.',
                        parent=self.root)
                    return
                register_explorer(exe)
                messagebox.showinfo('Explorer menu installed',
                    'The current Windows EXE is registered for your account.\n'
                    'Keep the EXE in this location or reinstall the menu after moving it.\n'
                    'Explorer opens the app in preview mode only.', parent=self.root)
            else:
                unregister_explorer()
                messagebox.showinfo('Explorer menu removed',
                    'The app-created right-click menu entries have been removed.', parent=self.root)
        except (OSError, ValueError) as exc:
            messagebox.showerror('Explorer integration error', str(exc), parent=self.root)

    def _browse(self):
        path = filedialog.askdirectory(parent=self.root, title='Choose folder to rename',
                                       initialdir=self.folder.get() if Path(self.folder.get()).is_dir() else str(Path.home()))
        if path:
            self.folder.set(path)

    def _start(self, label, worker):
        if self.processing:
            return
        self.processing = True
        self.current_operation = label
        self.state.set(label)
        self.summary.set('Please wait…')
        self._sync_controls()
        def run():
            try:
                result = worker()
                self.messages.put(('success', label, result))
            except Exception as exc:  # relay to Tk thread
                self.messages.put(('failure', label, exc))
        threading.Thread(target=run, daemon=False, name='greeklish-worker').start()

    def _drain_messages(self):
        while True:
            try:
                kind, label, value = self.messages.get_nowait()
            except queue.Empty:
                break
            if kind == 'scan_progress':
                folders, files, current = value
                self.scanning_counter = folders, files
                self.state.set('SCANNING')
                self.apply_meter_label.set(f'{folders:,} folders / {files:,} files')
                self.progress.set(f'Scanning folder {folders:,}: {str(current)[:125]}')
                continue
            if kind == 'progress':
                done, total, succeeded = value
                self.apply_meter.set(100 * done / total if total else 0)
                self.apply_meter_label.set(f'{done:,}/{total:,}  •  {100 * done / total:.0f}%')
                self.progress.set(f'Processed {done:,} of {total:,} names  •  {succeeded:,} renamed')
                self.state.set('APPLYING')
                continue
            if label == 'PREVIEW':
                self.progress_bar.stop()
                self.progress_bar.configure(mode='determinate')
            self.processing = False
            self.current_operation = None
            if kind == 'failure':
                if label == 'APPLY' and isinstance(value, PreviewChangedError):
                    self._invalidate()
                self.state.set('ERROR')
                self.summary.set(str(value))
                if label == 'APPLY':
                    self.apply_meter_label.set('Interrupted — review the CSV log')
                self.progress.set(f'Operation error: {value}')
                messagebox.showerror('Operation not completed', str(value), parent=self.root)
            elif label == 'PREVIEW':
                self.current_preview = value
                self.checked = {i: True for i in range(value.count)}
                self.manual_targets.clear()
                self.extension_overrides.clear()
                self._render_filtered_rows()
                self.state.set('PREVIEW READY' if value.count else 'NO CHANGES')
                self.summary.set('Untick to skip; double-click or select a row and Edit to change its proposed name.' if value.count else 'No names containing Greek letters need renaming.')
                self.progress.set(f'Scan finished: {self.scanning_counter[0]:,} folders, {self.scanning_counter[1]:,} files inspected. No files modified.')
                self.apply_meter.set(0)
                self.apply_meter_label.set('')
            elif label == 'APPLY':
                report: RenameReport = value
                self.current_preview = None
                self.checked.clear()
                self.manual_targets.clear()
                self.extension_overrides.clear()
                self.last_log = report.log
                self.state.set('STOPPED' if report.stopped else
                               'PARTIAL' if report.failed_count or report.skipped_count else 'COMPLETE')
                self.counter.set(f'{report.renamed_count:,} renamed / {report.selected_count:,} selected')
                self.summary.set(f'CSV undo log: {report.log.name}')
                if not report.stopped:
                    self.apply_meter.set(100)
                self.apply_meter_label.set(f'{report.processed_count:,}/{report.selected_count:,} processed'
                                           + (' — stopped' if report.stopped else ' • 100%'))
                self.progress.set(f'{report.renamed_count:,} renamed  •  {report.failed_count:,} failed'
                                  f'  •  {report.skipped_count:,} skipped  •  Undo: {report.log}')
                self._sync_controls()
                ResultsDialog(self.root, report)
            elif label == 'UNDO':
                restored, total = value
                self.current_preview = None
                self.checked.clear()
                self.manual_targets.clear()
                self.state.set('RESTORED' if restored == total else 'PARTIAL')
                self.summary.set(f'Restored {restored} of {total} recorded paths.')
                self.progress.set('Run Preview to see any remaining Greek filenames.')
                messagebox.showinfo('Undo result', f'Restored {restored} of {total} recorded paths.\nIf not all rows were restored, check for missing files or occupied original names.', parent=self.root)
            self._sync_controls()
        self.root.after(80, self._drain_messages)

    def _preview(self):
        path = self.folder.get().strip().strip('"')
        recursive = self.recursive.get()
        rename_folders = self.rename_folders.get()
        try:
            extensions = self._selected_extensions()
        except (ValueError, KeyError) as exc:
            messagebox.showerror('File-type filter', str(exc), parent=self.root)
            return
        self.scanning_counter = (0, 0)
        self.scan_last_update = 0.0
        self.apply_meter.set(0)
        self.apply_meter_label.set('Scanning folders…')
        self.progress_bar.configure(mode='indeterminate')
        self.progress_bar.start(12)

        def worker():
            def report(folders: int, files: int, current: Path) -> None:
                now = time.monotonic()
                if folders == 1 or now - self.scan_last_update > 0.1:
                    self.scan_last_update = now
                    self.messages.put(('scan_progress', 'PREVIEW', (folders, files, current)))
                else:
                    # The worker stores exact counts, but only the Tk thread
                    # may update widgets. Final callback is generated after scan.
                    pass
            latest = [0, 0, Path(path)]
            def tracked_report(folders, files, current):
                latest[:] = [folders, files, current]
                report(folders, files, current)
            answer = create_preview(path, recursive=recursive, rename_folders=rename_folders,
                                    file_extensions=extensions, scan_progress=tracked_report)
            if latest[0]:
                self.messages.put(('scan_progress', 'PREVIEW', tuple(latest)))
            return answer
        self._start('PREVIEW', worker)

    def _apply(self):
        preview = self.current_preview
        if preview is None or preview.count == 0:
            return
        selected = self._selected_operations()
        overrides = {preview.operations[i][0] for i in self.extension_overrides}
        try:
            selected = validate_selection(preview, selected, extension_overrides=overrides)
        except (InvalidSelectionError, PreviewChangedError) as exc:
            messagebox.showerror('Review selection', str(exc), parent=self.root)
            return
        count = len(selected)
        if not messagebox.askyesno('Confirm filename changes',
                    f'Rename {count} files/folders in:\n{preview.root}\n\nThis changes names, not file contents.\nA CSV undo log will be created.\n\nProceed?',
                    icon='warning', parent=self.root, default='no'):
            return
        self.stop_event.clear()
        self.apply_meter.set(0)
        self.apply_meter_label.set(f'0/{count:,} processed  •  0%')
        self.progress.set(f'Applying selected renames: 0 of {count:,} processed…')

        def worker():
            last_update = [0.0]
            def report(done: int, total: int, renamed: int) -> None:
                now = time.monotonic()
                # Throttle UI notifications for large batches; show first,
                # last, and updates roughly every 70ms while rename proceeds.
                if done == 1 or done == total or now - last_update[0] >= 0.07:
                    last_update[0] = now
                    self.messages.put(('progress', 'APPLY', (done, total, renamed)))
            return execute_preview_report(preview, selected=selected,
                      stop_requested=self.stop_event.is_set, progress_callback=report,
                      extension_overrides=overrides)
        self._start('APPLY', worker)

    def _export(self):
        plan = self.current_preview
        if plan is None or not plan.operations:
            return
        path = filedialog.asksaveasfilename(parent=self.root, title='Export rename preview',
                   defaultextension='.csv', filetypes=[('CSV files', '*.csv')],
                   initialfile='greeklish_preview.csv')
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as handle:
                writer = csv.writer(handle)
                writer.writerow(['selected', 'edited', 'type', 'original_relative_path', 'proposed_relative_path'])
                for i, (old, _automatic) in enumerate(plan.operations):
                    new = self._display_name(i)
                    writer.writerow(['yes' if self.checked[i] else 'no',
                                     'yes' if i in self.manual_targets else 'no',
                                     'folder' if old.is_dir() else 'file',
                                     str(old.relative_to(plan.root)), str(new.relative_to(plan.root))])
            self.progress.set(f'Preview exported (no names changed): {path}')
        except OSError as exc:
            messagebox.showerror('Export failed', str(exc), parent=self.root)

    def _undo(self):
        initial = str(self.last_log.parent) if self.last_log and self.last_log.exists() else self.folder.get()
        logfile = filedialog.askopenfilename(parent=self.root, title='Select Greeklish undo log',
                         initialdir=initial if Path(initial).is_dir() else str(Path.home()),
                         filetypes=[('CSV log', '*.csv'), ('All files', '*.*')])
        if not logfile:
            return
        root = self.folder.get().strip().strip('"')
        phrase = simpledialog.askstring('Undo names',
                'Restore filenames using this CSV log?\n\n'
                f'Folder: {root}\nLog: {logfile}\n\nType UNDO to continue:',
                parent=self.root)
        if phrase != 'UNDO':
            return
        self._start('UNDO', lambda: restore_log(root, logfile))


def main() -> int:
    parser = argparse.ArgumentParser(description='Greek to Greeklish Renamer desktop application')
    parser.add_argument('--folder', type=Path, help='Preselect a folder (Explorer menu: preview only)')
    parser.add_argument('--self-test', action='store_true', help='Run noninteractive EXE smoke test')
    parser.add_argument('--version', action='store_true', help='Display version')
    args = parser.parse_args()
    if args.self_test:
        return check_headless_build()
    if args.version:
        print(VERSION)
        return 0
    folder = None
    if args.folder is not None:
        requested = args.folder.expanduser()
        if requested.is_dir():
            folder = requested.resolve()
        else:
            parser.error('The Explorer-selected folder does not exist or is not accessible.')
    root = tk.Tk()
    window = GreeklishWindow(root, initial_folder=folder)
    if folder is not None:
        root.after(350, window._preview)  # Read-only preview, NEVER auto apply.
    root.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

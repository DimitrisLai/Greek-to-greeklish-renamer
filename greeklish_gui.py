#!/usr/bin/env python3
"""Greek to Greeklish Renamer 2.0 — native Windows desktop UI.

Built with Python's standard-library Tkinter. No Tk calls occur on worker threads.
The existing command-line renamer remains available separately.
"""
from __future__ import annotations

import csv
import io
import queue
import sys
import tempfile
import threading
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

from renamer_service import (PreviewChangedError, RenamePreview, create_preview,
                             execute_preview, restore_log)
from rename_greek_to_greeklish import VERSION

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
        preview = create_preview(root, recursive=False, rename_folders=False)
        if len(preview.operations) != 1:
            return 11
        changed, log = execute_preview(preview)
        if changed != 1 or not (root / 'Ellinika.mp3').exists():
            return 12
        count, total = restore_log(root, log)
        if (count, total) != (1, 1) or original.read_bytes() != b'unchanged media bytes':
            return 13
    return 0


class GreeklishWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f'Greek to Greeklish Renamer  |  {VERSION}')
        self.root.geometry('1050x730')
        self.root.minsize(820, 590)
        self.root.configure(background=PAPER)
        try:
            self.root.tk.call('tk', 'scaling', 1.2)
        except tk.TclError:
            pass

        self.folder = tk.StringVar(value=str(Path.home()))
        self.recursive = tk.BooleanVar(value=False)
        self.rename_folders = tk.BooleanVar(value=False)
        self.filter_text = tk.StringVar()
        self.summary = tk.StringVar(value='Select a folder and click Preview changes.')
        self.counter = tk.StringVar(value='0 proposed changes')
        self.state = tk.StringVar(value='READY')
        self.progress = tk.StringVar(value='No files have been modified.')
        self.current_preview: RenamePreview | None = None
        self.last_log: Path | None = None
        self.processing = False
        self.messages: queue.Queue = queue.Queue()
        self._configure_style()
        self._layout()
        self._bind_events()
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
        tk.Label(controls, text='Greek-free names are always skipped', bg=PAPER,
                 fg=MUTED, font=(FONT, 9)).pack(side='right')

        heading = tk.Frame(frame, bg=PAPER)
        heading.pack(fill='x', pady=(0, 9))
        tk.Label(heading, text='2   REVIEW PROPOSED CHANGES', bg=PAPER, fg=NAVY,
                 font=(FONT, 10, 'bold')).pack(side='left')
        tk.Label(heading, textvariable=self.counter, bg=PAPER, fg=TEAL,
                 font=(FONT, 10, 'bold')).pack(side='right')

        tablewrap = tk.Frame(frame, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
        tablewrap.pack(fill='both', expand=True)
        tablewrap.grid_rowconfigure(0, weight=1)
        tablewrap.grid_columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(tablewrap, style='Greek.Treeview', show='headings',
                                 columns=('kind', 'before', 'after'))
        self.tree.heading('kind', text='TYPE')
        self.tree.heading('before', text='CURRENT PATH')
        self.tree.heading('after', text='PROPOSED PATH')
        self.tree.column('kind', width=88, stretch=False, anchor='w')
        self.tree.column('before', width=390, minwidth=160, stretch=True)
        self.tree.column('after', width=390, minwidth=160, stretch=True)
        self.tree.tag_configure('odd', background='#F0F5F8')
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

        buttons = tk.Frame(frame, bg=PAPER)
        buttons.pack(fill='x', pady=(14, 0))
        self.preview_btn = self._button(buttons, 'Preview changes', self._preview, main=True, width=17)
        self.preview_btn.pack(side='left')
        self.apply_btn = self._button(buttons, 'Apply renames', self._apply, width=15)
        self.apply_btn.pack(side='left', padx=(9, 0))
        self.export_btn = self._button(buttons, 'Export preview', self._export, width=16)
        self.export_btn.pack(side='left', padx=(9, 0))
        self.undo_btn = self._button(buttons, 'Undo from CSV', self._undo, width=14)
        self.undo_btn.pack(side='right')

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
        self.rename_folders.trace_add('write', lambda *_: self._invalidate())

    def _change_recursion(self):
        if not self.recursive.get() and self.rename_folders.get():
            self.rename_folders.set(False)
        self._invalidate()

    def _invalidate(self):
        self.current_preview = None
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
        self.folder_check.configure(state='normal' if self.recursive.get() and not self.processing else 'disabled')
        self.rec_check.configure(state=state)
        may_apply = bool(self.current_preview and self.current_preview.count and not self.processing)
        self.apply_btn.configure(state='normal' if may_apply else 'disabled')
        self.export_btn.configure(state='normal' if may_apply else 'disabled')

    def _browse(self):
        path = filedialog.askdirectory(parent=self.root, title='Choose folder to rename',
                                       initialdir=self.folder.get() if Path(self.folder.get()).is_dir() else str(Path.home()))
        if path:
            self.folder.set(path)

    def _start(self, label, worker):
        if self.processing:
            return
        self.processing = True
        self.state.set(label)
        self.summary.set('Please wait…')
        self._sync_controls()
        def run():
            try:
                result = worker()
                self.messages.put(('success', label, result))
            except Exception as exc:  # relay to Tk thread
                self.messages.put(('failure', label, exc))
        threading.Thread(target=run, daemon=True, name='greeklish-worker').start()

    def _drain_messages(self):
        while True:
            try:
                kind, label, value = self.messages.get_nowait()
            except queue.Empty:
                break
            self.processing = False
            if kind == 'failure':
                if label == 'APPLY' and isinstance(value, PreviewChangedError):
                    self._invalidate()
                self.state.set('ERROR')
                self.summary.set(str(value))
                self.progress.set(f'No confirmed completion: {value}')
                messagebox.showerror('Operation not completed', str(value), parent=self.root)
            elif label == 'PREVIEW':
                self.current_preview = value
                self.tree.delete(*self.tree.get_children())
                for index, (old, new) in enumerate(value.operations):
                    kind_name = 'Folder' if old.is_dir() else 'File'
                    self.tree.insert('', 'end', values=(kind_name, str(old.relative_to(value.root)),
                                                        str(new.relative_to(value.root))),
                                     tags=('odd',) if index % 2 else ())
                self.counter.set(f'{value.count:,} proposed changes')
                self.state.set('PREVIEW READY' if value.count else 'NO CHANGES')
                self.summary.set('Review the full list before applying.' if value.count else 'No names containing Greek letters need renaming.')
                self.progress.set('Preview only. No files have been modified.')
            elif label == 'APPLY':
                renamed, log, count = value
                self.current_preview = None
                self.last_log = log
                self.state.set('COMPLETE' if renamed == count else 'PARTIAL')
                self.counter.set(f'{renamed:,} of {count:,} renamed')
                self.summary.set(f'CSV undo log: {log.name}')
                self.progress.set(f'{renamed}/{count} renamed  •  log: {log}')
                messagebox.showinfo('Rename completed' if renamed == count else 'Partial completion',
                                    f'{renamed} of {count} names renamed.\n\nUndo log:\n{log}\n\nKeep the CSV until you have checked the results.',
                                    parent=self.root)
            elif label == 'UNDO':
                restored, total = value
                self.current_preview = None
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
        self._start('PREVIEW', lambda: create_preview(path, recursive=recursive,
                                                      rename_folders=rename_folders))

    def _apply(self):
        preview = self.current_preview
        if preview is None or preview.count == 0:
            return
        count = preview.count
        if not messagebox.askyesno('Confirm filename changes',
                    f'Rename {count} files/folders in:\n{preview.root}\n\nThis changes names, not file contents.\nA CSV undo log will be created.\n\nProceed?',
                    icon='warning', parent=self.root, default='no'):
            return
        self._start('APPLY', lambda: (*execute_preview(preview), count))

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
                writer.writerow(['type', 'original_relative_path', 'proposed_relative_path'])
                for old, new in plan.operations:
                    writer.writerow(['folder' if old.is_dir() else 'file',
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
    if '--self-test' in sys.argv[1:]:
        return check_headless_build()
    if '--version' in sys.argv[1:]:
        print(VERSION)
        return 0
    root = tk.Tk()
    GreeklishWindow(root)
    root.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

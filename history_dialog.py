"""History window for Greek to Greeklish Renamer — separate, testable UI module."""
from __future__ import annotations
import csv
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from history_service import list_history, read_history

PAPER = '#F5F8FC'
NAVY = '#101E32'
TEAL = '#078F91'
TEXT = '#1C2D42'
MUTED = '#53687D'
WHITE = '#FFFFFF'
FONT = 'Segoe UI'


class HistoryDialog(tk.Toplevel):
    """Read-only local rename history; restoration still requires typed UNDO."""
    def __init__(self, parent, folder: str, on_undo):
        super().__init__(parent)
        self.root_folder = Path(folder).expanduser()
        self.on_undo = on_undo
        self.title('Previous renames — Greek to Greeklish Renamer')
        self.geometry('950x655')
        self.minsize(700, 480)
        self.configure(bg=PAPER)
        self.transient(parent)
        main = tk.Frame(self, bg=PAPER, padx=20, pady=15)
        main.pack(fill='both', expand=True)
        tk.Label(main, text='Rename and undo history', bg=PAPER, fg=NAVY,
                 font=(FONT, 16, 'bold')).pack(anchor='w')
        tk.Label(main, text=f'Folder: {self.root_folder}', bg=PAPER, fg=MUTED,
                 wraplength=850, anchor='w').pack(anchor='w', pady=(4, 10))
        tk.Label(main, text='Select a previous run to inspect the actual undo CSV. '
                 'Only logs saved directly in this folder are listed (latest 200).',
                 bg=PAPER, fg=TEXT, anchor='w', wraplength=850).pack(anchor='w')
        self.logs = ttk.Treeview(main, columns=('date','name','size'), show='headings',
                                  height=7, style='Greek.Treeview')
        for col, title, width in [('date','MODIFIED',170),('name','UNDO LOG',560),('size','SIZE',92)]:
            self.logs.heading(col, text=title)
            self.logs.column(col, width=width, stretch=col=='name', anchor='w')
        self.logs.pack(fill='x', pady=(12, 10))
        self.detail_text = tk.StringVar(value='Select a history entry to inspect its recorded changes.')
        tk.Label(main, textvariable=self.detail_text, bg=PAPER, fg=TEAL,
                 font=(FONT, 9, 'bold'), anchor='w').pack(fill='x', pady=(0, 6))
        holder = tk.Frame(main, bg=WHITE)
        holder.pack(fill='both', expand=True)
        self.detail_tree = ttk.Treeview(holder, columns=('old','new'), show='headings', style='Greek.Treeview')
        self.detail_tree.heading('old', text='ORIGINAL NAME')
        self.detail_tree.heading('new', text='RENAMED TO')
        self.detail_tree.column('old', width=420)
        self.detail_tree.column('new', width=420)
        self.detail_tree.pack(side='left', fill='both', expand=True)
        scroller = ttk.Scrollbar(holder, orient='vertical', command=self.detail_tree.yview)
        scroller.pack(side='right', fill='y')
        self.detail_tree.configure(yscrollcommand=scroller.set)
        tk.Label(main, text='History is based on CSV logs, not a system-wide database. '
                 'The current filesystem may differ from a previous run. Undo is checked again before restoring.',
                 bg=PAPER, fg=MUTED, wraplength=880, justify='left').pack(anchor='w', pady=(10, 5))
        actions = tk.Frame(main, bg=PAPER)
        actions.pack(fill='x')
        self.undo_btn = tk.Button(actions, text='Undo selected run…', command=self.undo_selected,
                      font=(FONT, 10, 'bold'), padx=12, pady=9, state='disabled')
        self.undo_btn.pack(side='left')
        tk.Button(actions, text='Close', command=self.destroy,
                  font=(FONT, 10, 'bold'), padx=12, pady=9).pack(side='right')
        self.logs.bind('<<TreeviewSelect>>', self.show_detail)
        self._entries = ()
        self._selected_log = None
        self._populate()
        self.grab_set()

    def _populate(self):
        try:
            self._entries = list_history(self.root_folder)
        except (OSError, ValueError) as exc:
            messagebox.showerror('History unavailable', str(exc), parent=self)
            self.destroy()
            return
        for i, item in enumerate(self._entries):
            self.logs.insert('', 'end', iid=str(i), values=(
                 item.modified.strftime('%Y-%m-%d %H:%M:%S'), item.path.name,
                 f'{item.bytes:,} B'))
        if self._entries:
            self.logs.selection_set('0')
            self.show_detail()
        else:
            self.detail_text.set('No previous undo logs found in this folder.')

    def show_detail(self, _event=None):
        selection = self.logs.selection()
        self._selected_log = None
        self.undo_btn.configure(state='disabled')
        self.detail_tree.delete(*self.detail_tree.get_children())
        if not selection:
            return
        log = self._entries[int(selection[0])].path
        try:
            detail = read_history(self.root_folder, log)
        except (OSError, ValueError, UnicodeError, csv.Error) as exc:
            self.detail_text.set('Cannot read selected log: ' + str(exc))
            return
        for i, (old, new) in enumerate(detail.preview_rows):
            self.detail_tree.insert('', 'end', iid=str(i), values=(old, new))
        note = f'{detail.changes:,} completed renames recorded'
        if detail.truncated:
            note += f'  •  showing first {len(detail.preview_rows):,}'
        self.detail_text.set(note)
        self._selected_log = log
        self.undo_btn.configure(state='normal' if detail.changes else 'disabled')

    def undo_selected(self):
        if self._selected_log is None:
            return
        log = self._selected_log
        self.destroy()
        self.on_undo(str(log))


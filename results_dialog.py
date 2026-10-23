"""Read-only detailed results display for the Greeklish GUI."""
from __future__ import annotations
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from renamer_service import RenameReport
from theme_support import colorize

PAPER = '#F5F8FC'
NAVY = '#101E32'
TEAL = '#078F91'
TEXT = '#1C2D42'
MUTED = '#53687D'
WHITE = '#FFFFFF'
FONT = 'Segoe UI'


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
        colorize(self, getattr(parent, '_greeklish_theme', 'Light'))
        self.grab_set()

    def export(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension='.csv',
                  initialfile='greeklish_result_report.csv', filetypes=[('CSV files','*.csv')])
        if path:
            try:
                self.report.export_csv(Path(path))
            except OSError as exc:
                messagebox.showerror('Export failed', str(exc), parent=self)


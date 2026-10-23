"""Pure Tkinter layout for the Greeklish desktop application.

Kept separate so window behavior stays testable and maintainable.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from gui_theme import *
from rename_greek_to_greeklish import VERSION

class WindowLayoutMixin:
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
        black = getattr(self, 'appearance', 'Light') == 'Black'
        background = '#151D29' if black else WHITE
        border = ('#55D8C9' if enabled else '#99AABD') if black else (TEAL if enabled else '#8798A7')
        icon.put(background, to=(0, 0, 20, 20))
        icon.put(border, to=(2, 2, 18, 18))
        icon.put(('#087F80' if black else TEAL) if enabled else background, to=(4, 4, 16, 16))
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
        self.theme_btn = self._button(top, 'Black theme', self._toggle_appearance, width=12)
        self.theme_btn.place(relx=0.73, y=25, anchor='e')

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
        self.history_btn = self._button(controls, 'History…', self._show_history, width=11)
        self.history_btn.pack(side='right', padx=(0, 9))

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
        self.cancel_scan_btn = self._button(buttons, 'Cancel scan', self._request_scan_cancel, width=12)
        self.cancel_scan_btn.pack(side='left', padx=(9, 0))
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


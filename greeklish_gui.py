#!/usr/bin/env python3
"""Greek to Greeklish Renamer 2.4.0 — native Windows desktop UI.

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
from rename_greek_to_greeklish import VERSION, ScanCancelled
from renamer_service import parse_extensions
from history_service import list_history, read_history
from history_dialog import HistoryDialog
from results_dialog import ResultsDialog
from csv_safety import spreadsheet_cell
from explorer_integration import register as register_explorer, unregister as unregister_explorer, executable_for_menu

from gui_theme import *  # shared palette and extension presets
from user_preferences import Preferences, load as load_preferences, save as save_preferences
from gui_layout import WindowLayoutMixin
from theme_support import colorize, configure_ttk, recolor_preview_tags


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
    # Verify bundled history service and no-overwrite behavior in frozen EXE.
    with tempfile.TemporaryDirectory(prefix='greeklish-gui-history-test-') as folder:
        root = Path(folder)
        greek = root / 'Αθήνα.mp3'
        greek.write_bytes(b'original')
        preview = create_preview(root, recursive=False, rename_folders=False)
        report = execute_preview_report(preview, preview.operations)
        entries = list_history(root)
        if len(entries) != 1 or read_history(root, entries[0].path).changes != 1:
            return 20
        if restore_log(root, entries[0].path) != (1, 1):
            return 21
        if greek.read_bytes() != b'original':
            return 22
    # Exercise cooperative cancellation within the frozen EXE itself.
    with tempfile.TemporaryDirectory(prefix='greeklish-gui-scan-cancel-') as folder:
        root = Path(folder)
        original = root / 'Ελληνικά.mp3'
        original.write_bytes(b'untouched')
        cancelled = threading.Event()
        def scanned(folders, files, current):
            cancelled.set()
        try:
            create_preview(root, recursive=False, rename_folders=False,
                           scan_progress=scanned, should_cancel=cancelled.is_set)
            return 23  # expected to abort before delivering a preview
        except ScanCancelled:
            pass
        if original.read_bytes() != b'untouched' or list(root.glob('greeklish_rename_log*')):
            return 24
        from user_preferences import save as persist, load as restore, Preferences as Pref
        settings = root / 'app_settings.json'
        if not persist(Pref(str(root), 'MP3 only', '.mp3'), settings):
            return 25
        if restore(settings).file_type_preset != 'MP3 only':
            return 26
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
        muted = '#abbacd' if getattr(self.parent, '_greeklish_theme', 'Light') == 'Black' else MUTED
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
                       foreground=muted, wraplength=480).pack(anchor='w', pady=(8, 4))
        else:
            self.allow_var.set(True)
            ttk.Label(master, text='Folder names can include periods.',
                      foreground=muted).pack(anchor='w', pady=(6, 4))
        return self.name_entry

    def buttonbox(self):
        super().buttonbox()
        colorize(self, getattr(self.parent, '_greeklish_theme', 'Light'))

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


class GreeklishWindow(WindowLayoutMixin):
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

        self.preferences = load_preferences()
        self.appearance = self.preferences.appearance
        self.root._greeklish_theme = self.appearance
        self._theme_originals = {}
        restored = self.preferences.last_folder if not initial_folder else str(initial_folder)
        self.folder = tk.StringVar(value=str(restored or Path.home()))
        self.recursive = tk.BooleanVar(value=False)
        self.rename_folders = tk.BooleanVar(value=False)
        self.extension_preset = tk.StringVar(value=self.preferences.file_type_preset)
        self.custom_file_types = tk.StringVar(value=self.preferences.custom_file_types)
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
        self.scan_cancel_event = threading.Event()
        self._settings_timer = None
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
        self._apply_appearance()
        self._bind_events()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self._drain_timer = self.root.after(80, self._drain_messages)

    def _apply_appearance(self):
        """Repaint existing widgets; do not rescan or discard the preview."""
        self.root._greeklish_theme = self.appearance
        configure_ttk(self.style, self.appearance)
        colorize(self.root, self.appearance, self._theme_originals)
        recolor_preview_tags(self.tree, self.appearance)
        self.checkbox_yes = self._checkbox_icon(True)
        self.checkbox_no = self._checkbox_icon(False)
        for iid in self.tree.get_children():
            self._refresh_row(int(iid))
        self.theme_btn.configure(text='Light theme' if self.appearance == 'Black' else 'Black theme')

    def _toggle_appearance(self):
        if self.processing:
            return
        self.appearance = 'Light' if self.appearance == 'Black' else 'Black'
        self._apply_appearance()
        self._schedule_settings_save()

    def _bind_events(self):
        self.folder.trace_add('write', lambda *_: (self._invalidate(), self._schedule_settings_save()))
        self.recursive.trace_add('write', lambda *_: self._change_recursion())
        self.tree.bind('<ButtonRelease-1>', self._row_click)
        self.tree.bind('<Double-1>', self._row_double_click)
        self.tree.bind('<space>', self._keyboard_toggle)
        self.tree.bind('<<TreeviewSelect>>', lambda *_: self._sync_controls())
        self.rename_folders.trace_add('write', lambda *_: self._invalidate())
        self.extension_preset.trace_add('write', lambda *_: (self._file_type_changed(), self._schedule_settings_save()))
        self.custom_file_types.trace_add('write', lambda *_: (self._custom_type_changed(), self._schedule_settings_save()))
        self.filter_text.trace_add('write', lambda *_: self._render_filtered_rows())
        self.view_filter.trace_add('write', lambda *_: self._render_filtered_rows())

    def _schedule_settings_save(self):
        # Debounce text input; all Tk calls are on the UI thread.
        if self._settings_timer is not None:
            self.root.after_cancel(self._settings_timer)
        self._settings_timer = self.root.after(700, self._save_settings)

    def _save_settings(self):
        self._settings_timer = None
        from user_preferences import safe_folder
        folder = safe_folder(self.folder.get().strip().strip('"'))
        if folder:
            self.preferences = Preferences(folder, self.extension_preset.get(), self.custom_file_types.get(), self.appearance)
        else:
            self.preferences = Preferences(self.preferences.last_folder, self.extension_preset.get(), self.custom_file_types.get(), self.appearance)
        save_preferences(self.preferences)

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
        for btn in (self.browse_btn, self.preview_btn, self.undo_btn, self.history_btn, self.theme_btn):
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
        self.cancel_scan_btn.configure(state='normal' if self.processing and self.current_operation == 'PREVIEW'
                                        and not self.scan_cancel_event.is_set() else 'disabled')
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
            if self.current_operation == 'PREVIEW':
                if messagebox.askyesno('Scan in progress',
                       'Cancel the scan? No filenames have been changed.\n\n'
                       'The app will stay open until scanning stops.', parent=self.root):
                    self._request_scan_cancel()
            elif self.current_operation == 'APPLY':
                if messagebox.askyesno('Rename still running',
                         'Renaming is in progress. Close is disabled to protect the undo log.\n\n'
                         'Request a safe stop after the current file?', parent=self.root):
                    self._request_stop()
            else:
                messagebox.showinfo('Please finish the operation',
                     'A scan or restore operation is still running. The window will stay open.',
                     parent=self.root)
            return
        if self._settings_timer is not None:
            self.root.after_cancel(self._settings_timer)
        if self._drain_timer is not None:
            self.root.after_cancel(self._drain_timer)
            self._drain_timer = None
        self._save_settings()
        self.root.destroy()

    def _request_scan_cancel(self):
        if not self.processing or self.current_operation != 'PREVIEW':
            return
        self.scan_cancel_event.set()
        self.summary.set('Cancelling scan… no files have been modified.')
        self.apply_meter_label.set('Cancelling scan…')
        self._sync_controls()

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

    def _show_history(self):
        if self.processing:
            return
        HistoryDialog(self.root, self.folder.get().strip().strip('"'), self._undo_log)

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
            if kind == 'failure' and label == 'PREVIEW' and isinstance(value, ScanCancelled):
                self.current_preview = None
                self.tree.delete(*self.tree.get_children())
                self.checked.clear()
                self.manual_targets.clear()
                self.extension_overrides.clear()
                self.state.set('SCAN CANCELLED')
                self.summary.set('Scan cancelled. No changes were applied.')
                self.counter.set('0 proposed changes')
                self.apply_meter_label.set('Scan cancelled')
                self.progress.set('Scan cancelled safely. No filenames changed.')
            elif kind == 'failure':
                if label == 'APPLY'  and isinstance(value, PreviewChangedError):
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
        self._drain_timer = self.root.after(80, self._drain_messages)

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
        self.scan_cancel_event.clear()
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
                                    file_extensions=extensions, scan_progress=tracked_report,
                                    should_cancel=self.scan_cancel_event.is_set)
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
                                     spreadsheet_cell(str(old.relative_to(plan.root))),
                                     spreadsheet_cell(str(new.relative_to(plan.root)))])
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
        self._undo_log(logfile)

    def _undo_log(self, logfile: str):
        if self.processing:
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

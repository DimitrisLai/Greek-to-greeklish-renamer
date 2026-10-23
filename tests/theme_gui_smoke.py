"""Interactive appearance smoke test (run with xvfb-run on Linux).

Tests display-only switching against a real Tkinter window. Never renames files.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tkinter as tk
from tkinter import ttk
from greeklish_gui import GreeklishWindow
from renamer_service import create_preview
from user_preferences import load
from history_dialog import HistoryDialog


with tempfile.TemporaryDirectory(prefix="greeklish-theme-test-") as td:
    home = Path(td)
    os.environ["XDG_CONFIG_HOME"] = str(home / "config")
    folder = home / "music"
    folder.mkdir()
    for name in ("Ελληνικά.mp3", "Αθήνα.flac", "Τραγούδι.wav"):
        (folder / name).write_bytes(b"do not change these contents")
    original_bytes = {p.name: p.read_bytes() for p in folder.iterdir()}
    root = tk.Tk()
    root.withdraw()
    window = GreeklishWindow(root, initial_folder=folder)
    assert window.appearance == "Light"
    window.current_preview = create_preview(folder, recursive=False, rename_folders=False)
    window.checked = {i: True for i in range(window.current_preview.count)}
    window.checked[0] = False
    window._render_filtered_rows()
    first_preview = window.current_preview
    first_selection = dict(window.checked)
    old_items = tuple(window.tree.get_children())
    assert old_items

    window._toggle_appearance()
    root.update_idletasks()
    assert window.appearance == "Black"
    assert window.current_preview is first_preview
    assert window.checked == first_selection
    assert tuple(window.tree.get_children()) == old_items
    assert str(window.tree.cget("style")) == "Greek.Treeview"
    assert window.theme_btn.cget("text") == "Light theme"
    assert window.checkbox_yes is not None

    dialog = HistoryDialog(root, str(folder), lambda log: None)
    root.update_idletasks()
    assert dialog.cget("background") == "#0b1018", dialog.cget("background")
    dialog.destroy()

    window._save_settings()
    assert load().appearance == "Black"
    window._toggle_appearance()
    assert window.appearance == "Light"
    assert window.current_preview is first_preview
    assert window.checked == first_selection
    window._toggle_appearance()
    window._on_close()

    other = tk.Tk()
    other.withdraw()
    restored = GreeklishWindow(other)
    assert restored.appearance == "Black"
    assert restored.extension_preset.get() == "All file types"
    restored._on_close()
    assert {p.name: p.read_bytes() for p in folder.iterdir()} == original_bytes
    print("PASS: theme switch, 3-file preview, selections, history dialog, settings restore, untouched files")

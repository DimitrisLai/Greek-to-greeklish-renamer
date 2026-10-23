"""Light / black appearance for the Tkinter renamer.

Only display properties are changed.  No scan plans or filesystem operations are
reconstructed when the user switches themes.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

THEMES = ("Light", "Black")

# Separate maps are essential: white text in the header must stay readable
# even though white *backgrounds* become dark surfaces.
BLACK_BACKGROUND = {
    "#f5f8fc": "#0b1018",
    "#ffffff": "#151d29",
    "#101e32": "#090d15",
    "#19304a": "#131e2c",
    "#e9f0f6": "#101723",
    "#e8f2f5": "#1b323a",
    "#dce5ee": "#314252",
    "#f0f5f8": "#182331",
    "#edf0f2": "#1d2734",
    "#e4f6f2": "#173732",
    "#078f91": "#087f80",
    "#057a7c": "#086c70",
    "#f0f0f0": "#0b1018",
    "systembuttonface": "#0b1018",
}
BLACK_FOREGROUND = {
    "#101e32": "#f4f7fc",
    "#19304a": "#e9f1f8",
    "#1c2d42": "#e3ecf7",
    "#53687d": "#abbacd",
    "#078f91": "#55d8c9",
    "#057a7c": "#44c2b5",
    "#b56d0a": "#f0b958",
    "#8798a7": "#99aabd",
    "#a8c5d6": "#b1c9d7",
    "#82ced0": "#73ddd3",
    "#ffffff": "#ffffff",
    "#000000": "#e3ecf7",
    "black": "#e3ecf7",
}


def translated(option: str, source: str, black: bool) -> str:
    """Pure transformation; only known light-theme colors are recolored."""
    if not black:
        return source
    value = str(source).strip().lower()
    if option in ("foreground", "activeforeground", "disabledforeground",
                  "insertbackground", "selectforeground"):
        return BLACK_FOREGROUND.get(value, source)
    if option in ("background", "activebackground", "highlightbackground",
                  "highlightcolor", "selectbackground", "readonlybackground",
                  "troughcolor"):
        if option == "highlightcolor" and value == "#078f91":
            return "#55d8c9"
        return BLACK_BACKGROUND.get(value, source)
    return source


def colorize(root: tk.Misc, mode: str, original: dict | None = None) -> dict:
    """Apply a theme to plain Tk widgets without destroying their state.

    Remember *original light* colors once and derive each theme from those
    originals; repeated switches cannot accumulate palette drift.
    """
    originals = original if original is not None else {}
    black = mode == "Black"
    options = (
        "background", "foreground", "activebackground", "activeforeground",
        "disabledforeground", "insertbackground", "selectbackground",
        "selectforeground", "highlightbackground", "highlightcolor",
        "readonlybackground", "troughcolor",
    )
    def visit(widget):
        if isinstance(widget, (tk.Tk, tk.Toplevel, tk.Frame, tk.Label,
                               tk.Button, tk.Entry, tk.Text, tk.Listbox,
                               tk.Canvas, tk.LabelFrame, tk.Checkbutton)):
            if widget not in originals:
                try:
                    available = set(widget.keys())
                    originals[widget] = {opt: widget.cget(opt) for opt in options
                                         if opt in available}
                except tk.TclError:
                    originals[widget] = {}
            for opt, initial in originals[widget].items():
                target = translated(opt, initial, black)
                try:
                    if widget.cget(opt) != target:
                        widget.configure(**{opt: target})
                except tk.TclError:
                    pass
        try:
            children = widget.winfo_children()
        except tk.TclError:
            children = []
        for child in children:
            visit(child)
    visit(root)
    return originals


def configure_ttk(style: ttk.Style, mode: str) -> None:
    """Contrast-correct headings, inputs, comboboxes, progress, scrollbars."""
    black = mode == "Black"
    surface = "#151d29" if black else "#ffffff"
    background = "#0b1018" if black else "#f5f8fc"
    foreground = "#e3ecf7" if black else "#1c2d42"
    muted = "#abbacd" if black else "#53687d"
    border = "#314252" if black else "#dce5ee"
    header = "#131e2c" if black else "#19304a"
    accent = "#55d8c9" if black else "#078f91"
    selected = "#204b50" if black else "#cce9e9"
    selected_fg = "#ffffff" if black else "#101e32"
    style.configure("Greek.Treeview", background=surface, fieldbackground=surface,
                    foreground=foreground, rowheight=31, font=("Segoe UI", 10),
                    borderwidth=0)
    style.configure("Greek.Treeview.Heading", background=header, foreground="#ffffff",
                    font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(12, 11))
    style.map("Greek.Treeview", background=[("selected", selected)],
              foreground=[("selected", selected_fg)])
    style.map("Greek.Treeview.Heading",
              background=[("active", header), ("pressed", header)],
              foreground=[("active", "#ffffff")])
    style.configure("Greek.TCheckbutton", background=background, foreground=foreground,
                    font=("Segoe UI", 10), padding=2)
    style.map("Greek.TCheckbutton", background=[("active", background)],
              foreground=[("disabled", muted), ("active", foreground)])
    style.configure("Greek.Horizontal.TProgressbar", troughcolor=border,
                    background=accent, bordercolor=border, thickness=5)
    style.configure("TEntry", foreground=foreground, fieldbackground=surface,
                    background=surface, insertcolor=foreground, bordercolor=border,
                    lightcolor=border, darkcolor=border)
    style.configure("TCombobox", foreground=foreground, fieldbackground=surface,
                    background=surface, arrowcolor=foreground, bordercolor=border,
                    lightcolor=border, darkcolor=border, selectbackground=surface,
                    selectforeground=foreground)
    style.map("TCombobox",
              fieldbackground=[("readonly", surface), ("disabled", background)],
              foreground=[("readonly", foreground), ("disabled", muted)],
              selectbackground=[("readonly", surface)],
              selectforeground=[("readonly", foreground)])
    style.configure("TLabel", background=background, foreground=foreground)
    style.configure("TCheckbutton", background=background, foreground=foreground)
    for name in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        style.configure(name, troughcolor=background, background=border,
                        arrowcolor=foreground, bordercolor=background,
                        lightcolor=border, darkcolor=border)
    # Windows Combobox drop-down is a separate listbox widget.
    if black:
        style.master.option_add("*TCombobox*Listbox.background", surface)
        style.master.option_add("*TCombobox*Listbox.foreground", foreground)
        style.master.option_add("*TCombobox*Listbox.selectBackground", selected)
        style.master.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
    else:
        style.master.option_add("*TCombobox*Listbox.background", "#ffffff")
        style.master.option_add("*TCombobox*Listbox.foreground", "#1c2d42")
        style.master.option_add("*TCombobox*Listbox.selectBackground", "#cce9e9")
        style.master.option_add("*TCombobox*Listbox.selectForeground", "#101e32")


def recolor_preview_tags(tree: ttk.Treeview, mode: str) -> None:
    if mode == "Black":
        tree.tag_configure("odd", background="#182331", foreground="#e3ecf7")
        tree.tag_configure("excluded", background="#1d2734", foreground="#99aabd")
        tree.tag_configure("custom", background="#173732", foreground="#e3ecf7")
    else:
        tree.tag_configure("odd", background="#f0f5f8", foreground="#1c2d42")
        tree.tag_configure("excluded", background="#edf0f2", foreground="#8695a4")
        tree.tag_configure("custom", background="#e4f6f2", foreground="#1c2d42")

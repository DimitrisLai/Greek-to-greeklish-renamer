"""Opt-in, per-user Windows Explorer directory context-menu integration.

Never runs a rename: Explorer only launches the GUI with a preselected folder.
Registration uses HKCU (no admin access), is idempotent, and reversible.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

MENU_NAME = 'GreeklishRenamer'
KEYS = (
    (r'Software\Classes\Directory\shell\GreeklishRenamer', '%1'),
    (r'Software\Classes\Directory\Background\shell\GreeklishRenamer', '%V'),
)


def launch_command(executable: str | Path, folder_placeholder: str) -> str:
    """Quote both fixed executable path and Explorer-provided directory path."""
    executable = str(Path(executable).resolve())
    if '"' in executable or '\n' in executable:
        raise ValueError('Invalid executable path.')
    if folder_placeholder not in ('%1', '%V'):
        raise ValueError('Unexpected Explorer folder token.')
    return f'"{executable}" --folder "{folder_placeholder}"'


def available() -> bool:
    return os.name == 'nt'


def register(executable: str | Path) -> None:
    if not available():
        raise OSError('Explorer integration is only available on Windows.')
    import winreg
    exe = Path(executable).resolve()
    if not exe.is_file():
        raise FileNotFoundError(f'The Windows executable was not found: {exe}')
    for key_name, folder_placeholder in KEYS:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_name, 0, winreg.KEY_WRITE) as menu:
            winreg.SetValueEx(menu, 'MUIVerb', 0, winreg.REG_SZ, 'Convert to Greeklish (preview)')
            winreg.SetValueEx(menu, 'Icon', 0, winreg.REG_SZ, f'{exe},0')
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_name + r'\command', 0, winreg.KEY_WRITE) as cmd:
            winreg.SetValueEx(cmd, '', 0, winreg.REG_SZ, launch_command(exe, folder_placeholder))


def unregister() -> None:
    if not available():
        raise OSError('Explorer integration is only available on Windows.')
    import winreg
    for key_name, _ in KEYS:
        for subkey in (key_name + r'\command', key_name):
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, subkey)
            except FileNotFoundError:
                pass


def executable_for_menu() -> Path | None:
    """Only offer registration for the portable compiled EXE, not Python.exe."""
    return Path(sys.executable).resolve() if getattr(sys, 'frozen', False) else None

"""Testable GUI adapter for the Greeklish Renamer command-line engine.

All filesystem mutations are delegated to the original renamer core.  A fresh
preview is required immediately before applying a GUI selection.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from rename_greek_to_greeklish import apply_plan, is_link_or_junction, plan_renames, undo

Operation = tuple[Path, Path]

class PreviewChangedError(RuntimeError):
    """The folder has changed since the preview; run Preview again."""


@dataclass(frozen=True)
class RenamePreview:
    root: Path
    recursive: bool
    rename_folders: bool
    operations: Tuple[Operation, ...]

    @property
    def count(self) -> int:
        return len(self.operations)

    @property
    def file_count(self) -> int:
        return sum(1 for old, _ in self.operations if old.is_file())

    @property
    def folder_count(self) -> int:
        return self.count - self.file_count


def create_preview(folder: str | Path, *, recursive: bool, rename_folders: bool) -> RenamePreview:
    selected = Path(folder).expanduser()
    if is_link_or_junction(selected):
        raise ValueError('Please select a real folder instead of a shortcut, link or junction.')
    root = selected.resolve(strict=True)
    if not root.is_dir() or is_link_or_junction(root):
        raise ValueError('Select a normal, accessible folder (not a symbolic link or junction).')
    # Folder names are renamed only if scanning recursively and explicitly selected.
    folder_names = bool(recursive and rename_folders)
    operations = tuple(plan_renames(root, recursive=bool(recursive), files_only=not folder_names))
    return RenamePreview(root, bool(recursive), folder_names, operations)


def execute_preview(preview: RenamePreview) -> tuple[int, Path]:
    """Validate the selected changes again; never silently run an outdated plan."""
    updated = create_preview(preview.root, recursive=preview.recursive, rename_folders=preview.rename_folders)
    if updated.operations != preview.operations:
        raise PreviewChangedError('The directory contents changed. Run Preview again before renaming.')
    if not preview.operations:
        raise ValueError('Nothing to rename; no CSV log is needed.')
    return apply_plan(preview.root, list(preview.operations))


def restore_log(folder: str | Path, csv_file: str | Path) -> tuple[int, int]:
    selected = Path(folder).expanduser()
    if is_link_or_junction(selected):
        raise ValueError('Please select a real folder instead of a shortcut, link or junction.')
    root = selected.resolve(strict=True)
    if not root.is_dir() or is_link_or_junction(root):
        raise ValueError('Select a normal, accessible folder.')
    return undo(root, Path(csv_file), confirmed=True)

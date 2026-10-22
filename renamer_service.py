"""Safe, testable adapter between the graphical UI and original rename engine.

The full automatic plan is retained for stale-preview detection. Individual
selections and manually edited destinations are validated before any changes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

from rename_greek_to_greeklish import apply_plan, is_link_or_junction, plan_renames, undo

Operation = tuple[Path, Path]


class PreviewChangedError(RuntimeError):
    """Filesystem changes require generating a fresh preview."""


class InvalidSelectionError(ValueError):
    """An edited or selected destination is unsafe or cannot be applied."""


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
    folder_names = bool(recursive and rename_folders)
    operations = tuple(plan_renames(root, recursive=bool(recursive), files_only=not folder_names))
    return RenamePreview(root, bool(recursive), folder_names, operations)


def validate_new_filename(filename: str, *, original: str) -> None:
    """Windows-compatible one-component destination. No implicit extension changes."""
    if not filename or filename in ('.', '..') or not filename.strip():
        raise InvalidSelectionError('Enter a filename or folder name.')
    if filename.endswith((' ', '.')):
        raise InvalidSelectionError('Windows names cannot end with a space or a period.')
    if any(ord(c) < 32 or c in '<>:"/\\|?*' for c in filename):
        raise InvalidSelectionError('The name contains a Windows-forbidden character.')
    if len(filename.encode('utf-16-le', 'surrogatepass')) // 2 > 255:
        raise InvalidSelectionError('The name is too long (255 UTF-16 characters maximum).')
    device = filename.split('.')[0].rstrip(' ').upper()
    if device in {'CON', 'PRN', 'AUX', 'NUL'} or (len(device) == 4 and device[:3] in ('COM', 'LPT') and device[-1] in '123456789¹²³'):
        raise InvalidSelectionError('This name is reserved by Windows.')
    if filename.casefold() == original.casefold():
        raise InvalidSelectionError('The destination must differ from the original name. Uncheck the row to skip it.')


def validate_selection(preview: RenamePreview, selected: Iterable[Operation]) -> tuple[Operation, ...]:
    """Validate selected rows and edits without modifying the filesystem.

    Preserve the original bottom-up operation order, require an unchanged source
    and directory, and reject any occupied or duplicate destination (including
    case-insensitive conflicts on Linux). An excluded descendant must never be
    indirectly moved by a selected folder rename.
    """
    original = {old: new for old, new in preview.operations}
    choices: dict[Path, Path] = {}
    for submitted_old, submitted_new in selected:
        # Windows temp directories sometimes use 8.3 aliases (RUNNER~1).
        # Preview uses the resolved, long path. Normalize caller-supplied paths
        # before matching so an equivalent path is not rejected or misapplied.
        old = Path(submitted_old).resolve(strict=False)
        new = Path(submitted_new)
        if old not in original or old in choices:
            raise InvalidSelectionError('Unknown or duplicate preview row. Run Preview again.')
        if new.parent.resolve(strict=False) != old.parent:
            raise InvalidSelectionError('Edit the filename only; moving files to other directories is not supported.')
        validate_new_filename(new.name, original=old.name)
        choices[old] = old.with_name(new.name)
    if not choices:
        raise InvalidSelectionError('No rows selected. Tick one or more rows before applying.')

    targets: set[tuple[str, str]] = set()
    for old, new in choices.items():
        if not old.exists() or is_link_or_junction(old):
            raise PreviewChangedError('A source has changed or disappeared. Run Preview again.')
        try:
            siblings = {entry.name.casefold() for entry in os.scandir(old.parent)}
        except OSError as exc:
            raise PreviewChangedError(f'Cannot inspect a folder: {exc}') from exc
        if new.name.casefold() in siblings:
            raise InvalidSelectionError(f'The proposed name is already in use: {new.name}')
        key = (str(old.parent).casefold(), new.name.casefold())
        if key in targets:
            raise InvalidSelectionError(f'More than one selected row uses the same proposed name: {new.name}')
        targets.add(key)

    selected_folders = [old for old in choices if old.is_dir()]
    if selected_folders:
        for old, _ in preview.operations:
            if old in choices:
                continue
            if any(old.is_relative_to(parent) and old != parent for parent in selected_folders):
                raise InvalidSelectionError(
                    'An unchecked item is inside a selected folder rename. '
                    'Uncheck its parent folder too, or select the item, to ensure it stays unchanged.'
                )
    return tuple((old, choices[old]) for old, _ in preview.operations if old in choices)


def execute_preview(preview: RenamePreview, selected: Iterable[Operation] | None = None) -> tuple[int, Path]:
    """Recheck the *full* original preview and validate the selected edited subset."""
    updated = create_preview(preview.root, recursive=preview.recursive, rename_folders=preview.rename_folders)
    if updated.operations != preview.operations:
        raise PreviewChangedError('The directory contents changed. Run Preview again before renaming.')
    plan = validate_selection(preview, preview.operations if selected is None else selected)
    return apply_plan(preview.root, list(plan))


def restore_log(folder: str | Path, csv_file: str | Path) -> tuple[int, int]:
    selected = Path(folder).expanduser()
    if is_link_or_junction(selected):
        raise ValueError('Please select a real folder instead of a shortcut, link or junction.')
    root = selected.resolve(strict=True)
    if not root.is_dir() or is_link_or_junction(root):
        raise ValueError('Select a normal, accessible folder.')
    return undo(root, Path(csv_file), confirmed=True)

"""Safe, testable adapter between the graphical UI and original rename engine.

The full automatic plan is retained for stale-preview detection. Individual
selections and manually edited destinations are validated before any changes.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple, Callable, Collection

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


def validate_new_filename(filename: str, *, original: str,
                          allow_extension_change: bool = False) -> None:
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
    if not allow_extension_change and Path(original).suffix.casefold() != Path(filename).suffix.casefold():
        raise InvalidSelectionError('File extension is protected. Enable the advanced option to change it.')
    if filename.casefold() == original.casefold():
        raise InvalidSelectionError('The destination must differ from the original name. Uncheck the row to skip it.')


def validate_selection(preview: RenamePreview, selected: Iterable[Operation], *,
                       extension_overrides: Collection[Path] = ()) -> tuple[Operation, ...]:
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
        validate_new_filename(new.name, original=old.name,
                              allow_extension_change=old.is_dir() or old in extension_overrides)
        choices[old] = old.with_name(new.name)
    if not choices:
        raise InvalidSelectionError('No rows selected. Tick one or more rows before applying.')

    targets: set[tuple[str, str]] = set()
    # Large batches may contain thousands of files in one directory: scan its
    # siblings once instead of once per file (quadratic on Windows disks).
    siblings_by_parent: dict[Path, set[str]] = {}
    for old, new in choices.items():
        if not old.exists() or is_link_or_junction(old):
            raise PreviewChangedError('A source has changed or disappeared. Run Preview again.')
        try:
            if old.parent not in siblings_by_parent:
                with os.scandir(old.parent) as entries:
                    siblings_by_parent[old.parent] = {entry.name.casefold() for entry in entries}
            siblings = siblings_by_parent[old.parent]
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


def execute_preview(preview: RenamePreview, selected: Iterable[Operation] | None = None,
                    *, progress_callback=None, extension_overrides: Collection[Path] = ()) -> tuple[int, Path]:
    """Recheck the *full* original preview and validate the selected edited subset."""
    updated = create_preview(preview.root, recursive=preview.recursive, rename_folders=preview.rename_folders)
    if updated.operations != preview.operations:
        raise PreviewChangedError('The directory contents changed. Run Preview again before renaming.')
    plan = validate_selection(preview, preview.operations if selected is None else selected,
                              extension_overrides=extension_overrides)
    return apply_plan(preview.root, list(plan), progress_callback=progress_callback)



@dataclass(frozen=True)
class RenameRecord:
    old: Path
    new: Path
    status: str
    reason: str = ''


@dataclass(frozen=True)
class RenameReport:
    root: Path
    log: Path
    rows: tuple[RenameRecord, ...]
    selected_count: int
    processed_count: int
    renamed_count: int
    skipped_count: int
    failed_count: int
    excluded_count: int
    remaining_count: int
    stopped: bool
    report_file: Path | None = None

    def export_csv(self, path: Path) -> None:
        with Path(path).open('w', newline='', encoding='utf-8-sig') as out:
            writer = csv.writer(out)
            writer.writerow(['status', 'reason', 'original_relative_path', 'proposed_relative_path'])
            for row in self.rows:
                writer.writerow([row.status, row.reason, str(row.old.relative_to(self.root)),
                                 str(row.new.relative_to(self.root))])


def execute_preview_report(preview: RenamePreview, selected: Iterable[Operation], *,
                           stop_requested: Callable[[], bool] | None = None,
                           progress_callback=None,
                           extension_overrides: Collection[Path] = ()) -> RenameReport:
    """Run safely with a per-file result. Returns an undo log even after a stop.

    The original CLI API and CSV undo format are unchanged. A safe stop is
    checked between operations; every completed rename is flushed to the log.
    """
    updated = create_preview(preview.root, recursive=preview.recursive,
                             rename_folders=preview.rename_folders)
    if updated.operations != preview.operations:
        raise PreviewChangedError('The directory contents changed. Run Preview again before renaming.')
    plan = validate_selection(preview, selected, extension_overrides=extension_overrides)
    outcomes: list[RenameRecord] = []

    def collect(old: Path, new: Path, status: str, reason: str) -> None:
        outcomes.append(RenameRecord(old, new, status, reason))

    renamed, log = apply_plan(preview.root, list(plan), progress_callback=progress_callback,
                              result_callback=collect, stop_requested=stop_requested)
    attempted = {record.old: record for record in outcomes}
    selected_by_old = dict(plan)
    all_rows = []
    for old, automatic in preview.operations:
        if old in attempted:
            all_rows.append(attempted[old])
        elif old in selected_by_old:
            all_rows.append(RenameRecord(old, selected_by_old[old], 'not processed',
                                         'Stopped safely before this item'))
        else:
            all_rows.append(RenameRecord(old, automatic, 'excluded', 'Unchecked in the preview'))
    report = RenameReport(
        root=preview.root, log=log, rows=tuple(all_rows), selected_count=len(plan),
        processed_count=len(outcomes), renamed_count=renamed,
        skipped_count=sum(row.status == 'skipped' for row in outcomes),
        failed_count=sum(row.status == 'failed' for row in outcomes),
        excluded_count=len(preview.operations)-len(plan),
        remaining_count=len(plan)-len(outcomes), stopped=len(outcomes)<len(plan),
    )
    # Keep a durable per-item report alongside the CSV undo log. A failure to
    # write the optional report must never discard the successful undo log.
    path = log.with_name(log.name.replace('greeklish_rename_log_', 'greeklish_result_log_'))
    try:
        report.export_csv(path)
    except OSError:
        return report
    return RenameReport(**{**report.__dict__, 'report_file': path})

def restore_log(folder: str | Path, csv_file: str | Path) -> tuple[int, int]:
    selected = Path(folder).expanduser()
    if is_link_or_junction(selected):
        raise ValueError('Please select a real folder instead of a shortcut, link or junction.')
    root = selected.resolve(strict=True)
    if not root.is_dir() or is_link_or_junction(root):
        raise ValueError('Select a normal, accessible folder.')
    return undo(root, Path(csv_file), confirmed=True)

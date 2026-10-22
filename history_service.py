"""Read-only, folder-scoped history of verified Greeklish undo logs.

No system-wide tracking, private filenames database, or external access.
The actual Undo operation still uses the existing validated restore engine.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from rename_greek_to_greeklish import is_link_or_junction

PREFIX = 'greeklish_rename_log_'
HEADER = ['old_relative_path', 'new_relative_path']
MAX_LOGS = 200
MAX_PREVIEW_ROWS = 2000
MAX_LOG_BYTES = 32 * 1024 * 1024


@dataclass(frozen=True)
class HistoryLog:
    path: Path
    modified: datetime
    bytes: int


@dataclass(frozen=True)
class HistoryDetail:
    log: HistoryLog
    changes: int
    preview_rows: tuple[tuple[str, str], ...]
    truncated: bool


def _root(folder: str | Path) -> Path:
    raw = Path(folder).expanduser()
    if is_link_or_junction(raw):
        raise ValueError('Choose a normal folder, not a link or junction.')
    root = raw.resolve(strict=True)
    if not root.is_dir() or is_link_or_junction(root):
        raise ValueError('The selected history folder is not accessible.')
    return root


def _allowed_log(root: Path, path: str | Path) -> Path:
    entry = Path(path)
    # Do not use the CSV as an arbitrary external file picker.
    if not entry.name.startswith(PREFIX) or not entry.name.endswith('.csv'):
        raise ValueError('Not a Greeklish Renamer undo log.')
    if is_link_or_junction(entry) or entry.resolve(strict=True).parent != root:
        raise ValueError('The history log must be a regular file in the selected folder.')
    if not entry.is_file():
        raise ValueError('The history entry is not a regular file.')
    return entry


def list_history(folder: str | Path, *, limit: int = MAX_LOGS) -> tuple[HistoryLog, ...]:
    """Find recent local logs without reading file contents (large-folder friendly)."""
    root = _root(folder)
    if not 1 <= limit <= MAX_LOGS:
        raise ValueError('Invalid history limit.')
    matches = []
    for item in root.iterdir():
        if not (item.name.startswith(PREFIX) and item.name.endswith('.csv')):
            continue
        if is_link_or_junction(item) or not item.is_file():
            continue
        try:
            stat = item.stat()
        except OSError:
            continue
        matches.append(HistoryLog(item, datetime.fromtimestamp(stat.st_mtime), stat.st_size))
    return tuple(sorted(matches, key=lambda x: (x.modified, x.path.name), reverse=True)[:limit])


def read_history(folder: str | Path, logfile: str | Path,
                 *, max_preview_rows: int = MAX_PREVIEW_ROWS) -> HistoryDetail:
    """Validate entire CSV while retaining only a bounded number of display rows."""
    root = _root(folder)
    path = _allowed_log(root, logfile)
    if path.stat().st_size > MAX_LOG_BYTES:
        raise ValueError('This undo log is too large for the history viewer. Use Undo from CSV.')
    if not 1 <= max_preview_rows <= MAX_PREVIEW_ROWS:
        raise ValueError('Invalid preview row limit.')
    shown: list[tuple[str, str]] = []
    count = 0
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != HEADER:
            raise ValueError('The selected CSV is not a valid Greeklish undo log.')
        for row in reader:
            old, new = row.get('old_relative_path'), row.get('new_relative_path')
            if not isinstance(old, str) or not isinstance(new, str) or not old or not new or None in row:
                raise ValueError('The history CSV contains incomplete or invalid rows.')
            # We only display paths here, but do not approve arbitrary absolute
            # or traversal paths even for a history preview.
            for rel in (old, new):
                relpath = Path(rel)
                if relpath.is_absolute() or not (root / relpath).resolve(strict=False).is_relative_to(root):
                    raise ValueError('The history CSV contains a path outside this folder.')
            count += 1
            if len(shown) < max_preview_rows:
                shown.append((old, new))
    stat = path.stat()
    return HistoryDetail(HistoryLog(path, datetime.fromtimestamp(stat.st_mtime), stat.st_size),
                         count, tuple(shown), count > max_preview_rows)

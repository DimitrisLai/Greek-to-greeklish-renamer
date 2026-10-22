#!/usr/bin/env python3
"""Safely rename Greek filenames and folders using ELOT 743-inspired ASCII rules.

Python 3.10+, standard library only. Rename ONLY names with Greek letters.
Interactive: choose folder, choose recursion, preview, explicitly confirm.
Logs each completed change, allowing reverse-order undo of a run.
"""

from __future__ import annotations

import argparse
import errno
import ctypes
import ctypes.util
import csv
import os
import stat
import sys
import unicodedata
from datetime import datetime
from typing import Callable
from pathlib import Path

# Windows terminal and redirected PowerShell output can default to cp1252,
# which cannot print Greek names. Explicitly choose Unicode-safe output.
def _configure_unicode_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="backslashreplace")
            except (OSError, ValueError, LookupError):
                pass


_configure_unicode_console()

VERSION = "2.3.0"

# Modern Greek -> ASCII transcription, inspired by ELOT 743 / ISO 843.
# This is NOT a certified, fully reversible implementation: accents are removed.
LETTERS = {
    "α": "a", "β": "v", "γ": "g", "δ": "d", "ε": "e", "ζ": "z",
    "η": "i", "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m",
    "ν": "n", "ξ": "x", "ο": "o", "π": "p", "ρ": "r", "σ": "s",
    "ς": "s", "τ": "t", "υ": "y", "φ": "f", "χ": "ch",
    "ψ": "ps", "ω": "o",
}
PAIRS = {"γγ": "ng", "γκ": "gk", "γξ": "nx", "γχ": "nch", "ου": "ou"}
VOWELS = set("αεηιουω")
VOICED = VOWELS | set("βγδζλμνρ")
ACCENTS = {"\u0300", "\u0301", "\u0342"}


def characters(text: str) -> list[str]:
    """Group each base code point with any subsequent combining marks."""
    result: list[str] = []
    for char in text:
        if unicodedata.combining(char) and result:
            result[-1] += char
        else:
            result.append(char)
    return result


def greek_info(unit: str) -> tuple[str, bool, bool] | None:
    """(lowercase base, accented, diaeresis), or None for non-Greek."""
    decomposed = unicodedata.normalize("NFD", unit)
    if not decomposed or decomposed[0].lower() not in LETTERS:
        return None
    return (
        decomposed[0].lower(),
        any(mark in ACCENTS for mark in decomposed[1:]),
        "\u0308" in decomposed[1:],
    )


def contains_greek_letters(name: str) -> bool:
    return any(greek_info(unit) is not None for unit in characters(name))


def latin_case(value: str, source: str, next_unit: str | None) -> str:
    if source.isupper():
        if next_unit and next_unit[0].islower():
            return value.capitalize()
        return value.upper()
    if source[0].isupper():
        return value[:1].upper() + value[1:]
    return value


def to_greeklish(text: str) -> str:
    units = characters(text)
    output: list[str] = []
    index = 0
    while index < len(units):
        first = greek_info(units[index])
        if first is None:
            output.append(units[index])
            index += 1
            continue

        second = greek_info(units[index + 1]) if index + 1 < len(units) else None
        pair = first[0] + second[0] if second else ""
        used = 1
        if pair in ("αυ", "ευ", "ηυ") and not first[1] and not second[2]:
            following = greek_info(units[index + 2]) if index + 2 < len(units) else None
            suffix = "v" if following and following[0] in VOICED else "f"
            value = {"αυ": "a", "ευ": "e", "ηυ": "i"}[pair] + suffix
            used = 2
        elif pair == "μπ":
            before_is_letter = index > 0 and units[index - 1][0].isalpha()
            after_is_letter = index + 2 < len(units) and units[index + 2][0].isalpha()
            value = "mp" if before_is_letter and after_is_letter else "b"
            used = 2
        elif pair in PAIRS:
            value = PAIRS[pair]
            used = 2
        else:
            value = LETTERS[first[0]]
        source = "".join(units[index:index + used])
        next_unit = units[index + used] if index + used < len(units) else None
        output.append(latin_case(value, source, next_unit))
        index += used
    return "".join(output)


def converted_name(name: str, is_dir: bool) -> str:
    """Preserve already-Latin extension spelling and punctuation."""
    if is_dir:
        return to_greeklish(name)
    parts = Path(name)
    return to_greeklish(parts.stem) + to_greeklish(parts.suffix)


def available_name(desired: str, occupied: set[str], is_dir: bool) -> str:
    if desired.casefold() not in occupied:
        return desired
    parts = Path(desired)
    stem, suffix = (desired, "") if is_dir else (parts.stem, parts.suffix)
    number = 2
    while True:
        candidate = f"{stem} ({number}){suffix}"
        if candidate.casefold() not in occupied:
            return candidate
        number += 1


def is_occupied(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def is_link_or_junction(path: Path) -> bool:
    """Never traverse or rename symlinks and Windows reparse points.

    The reparse-point check also works on Python 3.10/3.11, where
    Path.is_junction() is not available yet.
    """
    try:
        if path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)()):
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except OSError:
        # An unreadable entry is safer to skip than to follow accidentally.
        return True


def plan_renames(root: Path, recursive: bool = False, files_only: bool = False, *,
                 file_extensions: frozenset[str] | None = None, scan_progress=None) -> list[tuple[Path, Path]]:
    """Produce a deterministic bottom-up plan; never change Latin-only names."""
    root = Path(root)
    plan: list[tuple[Path, Path]] = []
    scanned_folders = 0
    scanned_files = 0

    def report_scan(folder: Path, file_count: int) -> None:
        nonlocal scanned_folders, scanned_files
        scanned_folders += 1
        scanned_files += file_count
        if scan_progress is not None:
            scan_progress(scanned_folders, scanned_files, folder)

    if recursive:
        # Prune junctions/reparse points before descending, *then* reverse
        # the collected walk so that child entries precede parent folders.
        # os.walk(topdown=False) cannot safely prune these directories.
        collected = []
        def on_scan_error(exc: OSError) -> None:
            print(f"[SKIP] Cannot scan folder: {exc}")

        for folder_string, folders, files in os.walk(
            root, topdown=True, followlinks=False, onerror=on_scan_error
        ):
            folder = Path(folder_string)
            safe_folders = [
                name for name in folders
                if not is_link_or_junction(folder / name)
            ]
            folders[:] = safe_folders
            report_scan(folder, len(files))
            collected.append((folder_string, safe_folders, files))
        walk = reversed(collected)
    else:
        try:
            with os.scandir(root) as entries:
                files = [entry.name for entry in entries if entry.is_file(follow_symlinks=False)]
        except OSError as exc:
            print(f"[SKIP] Cannot open folder {root}: {exc}")
            return []
        report_scan(root, len(files))
        walk = [(str(root), [], files)]

    for folder_string, folders, files in walk:
        folder = Path(folder_string)
        try:
            occupied = {item.name.casefold() for item in folder.iterdir()}
        except OSError as exc:
            print(f"[SKIP] Cannot read {folder}: {exc}")
            continue
        items = [(name, False) for name in files]
        if recursive and not files_only:
            items.extend((name, True) for name in folders)
        for name, is_dir in sorted(items, key=lambda item: (item[0].casefold(), item[0])):
            if not is_dir and file_extensions is not None and Path(name).suffix.casefold() not in file_extensions:
                continue
            if not contains_greek_letters(name):
                continue
            old = folder / name
            if is_link_or_junction(old):
                continue
            desired = converted_name(name, is_dir)
            if desired == name:
                continue
            chosen = available_name(desired, occupied, is_dir)
            occupied.add(chosen.casefold())
            plan.append((old, folder / chosen))
    return plan


def ensure_in_root(path: Path, root: Path) -> None:
    if not path.resolve(strict=False).is_relative_to(root.resolve()):
        raise ValueError(f"Undo path outside target folder: {path}")


def undo(root: Path, log_file: Path, *, confirmed: bool = False) -> tuple[int, int]:
    """Reverse CSV entries so renamed folders are restored before their children."""
    log_file = Path(log_file).expanduser().resolve()
    if not log_file.is_file():
        raise FileNotFoundError(f"Undo log not found: {log_file}")
    with log_file.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["old_relative_path", "new_relative_path"]:
            raise ValueError("This is not a Greeklish Renamer undo CSV log")
        rows = list(reader)

    # Validate ALL rows before touching the filesystem.
    for row in rows:
        old_relative = Path(row["old_relative_path"])
        new_relative = Path(row["new_relative_path"])
        if old_relative.is_absolute() or new_relative.is_absolute():
            raise ValueError("Unsafe absolute path in undo log")
        ensure_in_root(root / old_relative, root)
        ensure_in_root(root / new_relative, root)

    print(f"Undo log: {log_file}")
    print(f"Folder:   {root}")
    print(f"Recorded changes: {len(rows)}")
    if not confirmed:
        if read_answer("Type UNDO to restore these names (anything else cancels): ") != "UNDO":
            print("Undo cancelled.")
            return (0, len(rows))

    restored = 0
    for row in reversed(rows):
        old = root / row["old_relative_path"]
        new = root / row["new_relative_path"]
        if not is_occupied(new):
            print(f"[SKIP] Missing: {new}")
            continue
        if is_occupied(old):
            print(f"[SKIP] Already occupied: {old}")
            continue
        try:
            rename_no_overwrite(new, old)
            print(f"[UNDO] {new.relative_to(root)} -> {old.relative_to(root)}")
            restored += 1
        except OSError as exc:
            print(f"[ERROR] {new.name}: {exc}")
    print(f"\nRestored: {restored}/{len(rows)}")
    return (restored, len(rows))


def read_answer(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return ""


def choose_folder(default: Path) -> Path | None:
    """Ask for a directory first; Enter uses the launcher/script folder."""
    print("Paste a folder path or drag a folder into this window.")
    print(f"Press ENTER to use: {default}\n")
    while True:
        answer = read_answer("Folder path: ")
        if not answer:
            root = default
        else:
            root = Path(answer.strip().strip('"').strip("' ")).expanduser()
        try:
            root = root.resolve()
        except OSError as exc:
            print(f"Invalid path: {exc}\n")
            continue
        if root.is_dir():
            return root
        print("That folder does not exist. Try again, or press ENTER for the default.\n")


def choose_recursion() -> bool:
    while True:
        response = read_answer("Include subdirectories and rename Greek folder names? [y/N]: ").lower()
        if response in ("", "n", "no"):
            return False
        if response in ("y", "yes"):
            return True
        print("Please type Y or N.")


def rename_no_overwrite(old: Path, new: Path) -> None:
    """Atomically refuse an occupied destination, even in a filesystem race.

    Windows os.rename already refuses replacement; Linux renameat2 with
    RENAME_NOREPLACE supplies the same property for both files and folders.
    Other POSIX systems fail closed rather than risk overwriting data.
    """
    if os.name == 'nt':
        os.rename(old, new)
        return
    if sys.platform.startswith('linux'):
        libc = ctypes.CDLL(None, use_errno=True)
        renameat2 = getattr(libc, 'renameat2', None)
        if renameat2 is not None:
            renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p,
                                  ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
            renameat2.restype = ctypes.c_int
            rc = renameat2(-100, os.fsencode(old), -100, os.fsencode(new), 1)
            if rc == 0:
                return
            error = ctypes.get_errno()
            if error not in (errno.ENOSYS, errno.EINVAL, errno.EOPNOTSUPP):
                raise OSError(error, os.strerror(error), str(new))
    raise OSError(errno.ENOTSUP,
                  'Atomic no-overwrite rename is not supported on this filesystem.', str(new))


def apply_plan(root: Path, plan: list[tuple[Path, Path]], *, progress_callback=None,
               result_callback=None, stop_requested: Callable[[], bool] | None = None) -> tuple[int, Path]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    logfile = root / f"greeklish_rename_log_{stamp}.csv"
    renamed = 0
    with logfile.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["old_relative_path", "new_relative_path"])
        handle.flush()
        completed = 0
        for old, new in plan:
            # A stop is honored ONLY between filesystem operations. Never kill
            # an in-flight rename or leave its CSV undo entry unwritten.
            if stop_requested is not None and stop_requested():
                break
            status, reason = 'renamed', ''
            try:
                if not is_occupied(old):
                    status, reason = 'skipped', 'Source no longer exists'
                    print(f"[SKIP] Source missing: {old}")
                elif is_occupied(new):
                    status, reason = 'skipped', 'Destination is already occupied'
                    print(f"[SKIP] Destination taken: {new}")
                else:
                    try:
                        rename_no_overwrite(old, new)
                        writer.writerow([str(old.relative_to(root)), str(new.relative_to(root))])
                        handle.flush()
                        renamed += 1
                    except OSError as exc:
                        status = 'skipped' if isinstance(exc, FileExistsError) or exc.errno == errno.EEXIST else 'failed'
                        reason = ('Destination became occupied during rename' if status == 'skipped'
                                  else f'{type(exc).__name__}: {exc}')
                        print(f"[ERROR] {old.name}: {exc}")
            finally:
                completed += 1
                if result_callback is not None:
                    try:
                        result_callback(old, new, status, reason)
                    except Exception as exc:
                        # A reporting callback cannot interrupt renaming.
                        print(f"[WARN] Result reporting failed: {exc}")
                if progress_callback is not None:
                    try:
                        progress_callback(completed, len(plan), renamed)
                    except Exception as exc:
                        print(f"[WARN] Progress reporting failed: {exc}")
    return (renamed, logfile)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Greek -> Greeklish safe batch renamer")
    parser.add_argument("--path", type=Path, default=None,
                        help="Choose a folder without the interactive folder question")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--recursive", action="store_true", help="Include subfolders without asking")
    scope.add_argument("--no-recursive", action="store_true", help="Only current folder, without asking")
    parser.add_argument("--files-only", action="store_true", help="Keep folder names unchanged")
    parser.add_argument("--dry-run", action="store_true", help="Preview without renaming")
    parser.add_argument("--yes", action="store_true", help="Confirm renames without asking")
    parser.add_argument("--undo", type=Path, metavar="CSV", help="Undo using a previous CSV log")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    args = parser.parse_args(argv)

    print("=" * 50)
    print(f"   GREEK TO GREEKLISH RENAMER v{VERSION}")
    print("=" * 50)
    print("Changes NAMES only, never file contents.\n")
    default = Path(__file__).resolve().parent
    if args.path is None:
        root = choose_folder(default)
        if root is None:
            return 1
    else:
        root = args.path.expanduser().resolve()
        if not root.is_dir():
            parser.error(f"Folder does not exist: {root}")
    print(f"Selected folder: {root}\n")

    if args.undo is not None:
        try:
            undo(root, args.undo, confirmed=args.yes)
        except (OSError, ValueError) as exc:
            print(f"[ERROR] Undo failed: {exc}", file=sys.stderr)
            return 1
        return 0

    recursive = args.recursive or (not args.no_recursive and choose_recursion())
    print(f"Subdirectories: {'YES' if recursive else 'NO'}")
    print("Rule: rename only names containing Greek characters.\n")
    plan = plan_renames(root, recursive=recursive, files_only=args.files_only)
    if not plan:
        print("No Greek filenames or folders found that need renaming.")
        print("Nothing was modified.")
        return 0
    for old, new in plan[:80]:
        print(f"  {old.relative_to(root)}  -->  {new.name}")
    if len(plan) > 80:
        print(f"  ... plus {len(plan) - 80} more changes")
    print(f"\nProposed changes: {len(plan)}")
    if args.dry_run:
        print("Preview only: nothing was modified.")
        return 0
    if not args.yes and read_answer("Type YES to apply these renames (anything else cancels): ") != "YES":
        print("Cancelled. Nothing was modified.")
        return 0
    try:
        renamed, log = apply_plan(root, plan)
    except OSError as exc:
        print(f"[ERROR] Could not create undo log: {exc}", file=sys.stderr)
        return 1
    print(f"\nRenamed: {renamed}/{len(plan)}")
    print(f"Undo CSV: {log}")
    print(f'To undo: py "{Path(__file__).resolve()}" --path "{root}" --undo "{log}"')
    return 0 if renamed == len(plan) else 1


if __name__ == "__main__":
    raise SystemExit(main())

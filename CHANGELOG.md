# Changelog

## [2.1.0] — 2026-10-22

- Added per-row checkboxes to selectively apply proposed renames (all checked by default).
- Added Select All / Select None and keyboard Space toggling for the preview list.
- Added Edit selected dialog and double-click editing of proposed filenames/folders.
- Added Windows filename validation, duplicate/collision checks, and protection for unchecked descendants of renamed folders.
- Re-validate the original full preview and edited selected subset immediately before applying.
- Updated CSV preview export to include selected and manually edited flags; CSV undo still includes only performed changes.
- Added regression tests and EXE smoke testing for selective and manually edited renames.
- Preserved the existing CLI and retained historical v2.0.0 release.

## [2.0.0] — 2026-10-21

- Added a complete Windows desktop user interface, using Tkinter with zero runtime dependencies.
- Released a standalone Windows EXE built by PyInstaller and tested with a headless rename/undo smoke test.
- Added independent subdirectory and folder-name rename controls.
- Added a preview table, progress/status feedback, CSV preview export and undo from CSV.
- Added a stale-preview safety check before applying changes.
- Added testable UI service layer and extra regression cases (previous CLI functions retained).
- Rebuilt the public manual and release packaging for the new GUI and CLI editions.

## [1.2.1] — 2026-10-18
- Fixed Unicode output on Windows terminals that default to cp1252.
- Added Windows regression checks and updated published PDF documentation.

## [1.2.0] — 2026-10-18
- Added directory selection, optional subdirectories, collision-safe renaming, preview and CSV undo.

## [1.1.0] — 2026-10-18
- Added subdirectory question and Greek-character detection.

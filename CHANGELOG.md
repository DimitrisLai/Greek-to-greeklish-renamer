# Changelog

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

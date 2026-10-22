# Changelog

## v2.3.0 (2026-10-22)
- Added History… browser of undo CSV runs saved in the selected folder, with recorded-name preview and explicitly confirmed undo.
- Added atomic no-replace protection to rename and undo operations on Windows and Linux; safe failure on unsupported filesystems.
- Protected informational preview/results CSV exports from spreadsheet formula interpretation, retaining lossless legacy undo CSVs.
- Added regression tests for history parsing, malicious/external CSV paths, overwrite races and CSV sanitization.
- Preserved audio filters, scan/apply progress, Explorer integration, version metadata and original CLI.

## v2.2.0 (2026-10-22)
- Added file-type filters, custom extension lists and animated scan progress.
- Added Windows icon and product version metadata, SHA-256 release digests.
- Added optional per-user Explorer right-click preview integration.

## [2.1.1] — 2026-10-22

- Replaced the two bulk-selection buttons with one dynamic **Select All / Select None** toggle.
- Replaced font-dependent checkboxes with a visible per-row checkbox image in the INCLUDE column.
- Added a determinate progress bar and processed/total, percent and successful rename counters while Apply runs.
- Progress callbacks also count skipped attempts correctly; CLI and CSV undo remain backward compatible.
- Optimized collision validation for large batches by caching sibling names per directory.
- Added progress-focused regression tests, including a 1,000-file selective rename and undo test.
- Updated Windows source and build documentation and the 10-page PDF manual.

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

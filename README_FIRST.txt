GREEK TO GREEKLISH RENAMER v2.3.0
Created by Dimitris Laidis | MIT License

WINDOWS DESKTOP APP (no Python needed)
--------------------------------------
1. Extract all files from the official Windows release ZIP.
2. Double-click GreeklishRenamer.exe.
3. Click Browse and select a directory containing Greek filenames.
4. Choose whether to include subdirectories and rename Greek folder names.
5. Click Preview changes and review the table.
6. All preview rows start checked. Untick rows that must stay unchanged.
7. Select a row and click Edit selected (or double-click it) to manually fix the proposed name.
8. Use the single Select None / Select All toggle above the preview table.
   Click an INCLUDE checkbox to toggle a single file independently.
9. Click Apply renames only after reviewing selected changes.
   Watch the live progress bar, percentage and processed/renamed counters.
10. Keep the CSV undo log created inside the selected folder.

The application only changes FILE AND FOLDER NAMES. It does not change media
contents or download/upload filenames to any service.

The new GUI provides a CSV preview export and Undo from CSV button.
Always back up important folders before bulk renames.

ALTERNATIVE (source ZIP, requires Python 3.10+):
  py greeklish_gui.py
  py rename_greek_to_greeklish.py

Official project and downloads:
https://github.com/DimitrisLai/Greek-to-greeklish-renamer

Custom edits are filename-only; the app will refuse collisions and unsafe Windows names.
If you untick a file inside a folder that is also selected to rename, untick
that parent folder too, so the excluded file's location remains unchanged.

PREVIOUS FEATURES (v2.1.2): Search/filter proposed filenames; edit names with extensions protected by default; Stop safely between renames; see a complete Results report with an automatically saved CSV.
Do not close the window while renames are running. Use Stop safely instead. Undo logs include completed changes only.

NEW IN 2.3.0:
- Use File Types: All, Audio, MP3, FLAC, WAV or Custom (.mp3, .flac).
- Scanning shows a moving indicator and number of folders/files inspected.
- Explorer menu... lets you install or remove an optional folder context-menu command.
  Windows 11: Show more options. This command ONLY opens a preview.
  Keep the extracted EXE in one location; reinstall after moving it.
- Windows icon/version details identify the EXE.
- Check SHA256SUMS.txt from the official GitHub release to verify downloads.
- File-type filtering disables folder renaming to protect unrelated files.

HISTORY (v2.3.0): Click History… to browse undo logs in your chosen folder, inspect names, and restore a chosen run after typing UNDO.
CSV SAFETY: Informational preview and results exports protect formula-like filenames. Undo logs retain exact paths.

GREEK TO GREEKLISH RENAMER v2.1.0
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
8. Use Select All / Select None for bulk selection.
9. Click Apply renames only after reviewing selected changes.
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

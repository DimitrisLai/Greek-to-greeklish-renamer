# Greek to Greeklish Renamer v2.1.2 — Safe Batch Control

**Dimitris Laidis · MIT License**

## Improvements

- **Stop safely:** Request a stop during Apply; the current filename operation finishes and its undo log entry is flushed before processing stops. Closing the window during Apply offers a safe stop instead of ending the process abruptly. Other in-progress operations also block accidental window closure.
- **Detailed results:** After Apply, view the renamed, skipped, failed, excluded and not-processed entries with individual reasons. Save or export a results CSV (`greeklish_result_log_*.csv`); the original compatible undo CSV remains available for every completed rename.
- **Extension protection:** Manual filename editing keeps `.mp3`, `.flac`, etc. protected by default. Users may explicitly check **Allow file extension change (advanced)** when needed. Safety and collision validations still apply.
- **Search and filters:** Find text in the original or proposed path, or show All / Included / Excluded / Edited. Filtering never changes the selected renames; Select All / None continues to work across the entire preview.

## Existing features

Safe Greek-to-Greeklish transliteration; selective preview and individual checkboxes; corrected filenames; recursive scanning with optional folder renames; conflict protection; background progress bar and percentage; CSV undo; standalone Windows EXE. The original command-line script is retained.

## Distribution

- `Greeklish-Renamer-v2.1.2-Windows-Dimitris-Laidis.zip` — standalone Windows EXE and PDF manual.
- `Greeklish-Renamer-v2.1.2-Source-Dimitris-Laidis.zip` — complete Python GUI/CLI sources, documentation and automated tests.
- `Greek_to_Greeklish_Renamer_User_Manual_v2.1.2_Dimitris_Laidis.pdf` — standalone 10-page manual.

Back up important directories before processing. Undo is best effort if files are subsequently moved or changed. The application operates locally; the current executable is not signed with a verified SignPath certificate.

**Source:** https://github.com/DimitrisLai/Greek-to-greeklish-renamer

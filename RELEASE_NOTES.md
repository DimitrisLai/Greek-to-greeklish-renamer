# Greek to Greeklish Renamer v2.3.0 — History & Collision Safety

**Dimitris Laidis · MIT License**

This release adds a built-in, read-only History browser for previous rename runs saved in the selected folder. Users can inspect recorded original and new names, then request restoration of a selected run using the existing exact `UNDO` confirmation. Logs remain regular CSV files; no online accounts, telemetry or new history database are introduced.

**Collision hardening:** the actual rename and undo operations now request atomic no-overwrite filesystem moves to avoid replacement if a destination becomes occupied after preview checks. An unsupported filesystem reports an error instead of risking an overwrite.

**CSV export hardening:** preview and detailed-results CSV exports escape spreadsheet-formula-like values. Undo CSVs intentionally retain literal names for backward-compatible, accurate restoration.

**Retained features:** selective checkboxes, manual corrections, extension protection, large-batch safe stop and progress, detailed reports, audio filters, scan indicator, Explorer right-click preview, original CLI, branded icon and version metadata.

## Downloads

- `Greeklish-Renamer-v2.3.0-Windows-Dimitris-Laidis.zip` — standalone Windows EXE with PDF/manual.
- `Greeklish-Renamer-v2.3.0-Source-Dimitris-Laidis.zip` — full source and tests.
- `Greek_to_Greeklish_Renamer_User_Manual_v2.3.0_Dimitris_Laidis.pdf` — 10-page user manual.
- `SHA256SUMS.txt` — SHA-256 verification for the three artifacts.

**Security note:** the Windows executable is not digitally signed until a signing provider approves and signs it. This release does not claim signing or SmartScreen reputation.

Project: https://github.com/DimitrisLai/Greek-to-greeklish-renamer

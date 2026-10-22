# Greek to Greeklish Renamer v2.1.1 — Checkboxes and Progress Edition

**Created by Dimitris Laidis · MIT License**

## Improvements in v2.1.1

- **One Select All / Select None toggle** now replaces the two separate buttons. It automatically changes its label according to whether all rows are selected.
- **Visible checkbox graphics** next to every preview row, not font-dependent checkmark characters. Click each checkbox to include or exclude one file independently.
- **Live Apply progress bar**, percentage, processed/total counter and successful rename count. Applying hundreds or thousands of names no longer leaves an ambiguous "Applying" state.
- **Large batch speedup:** directory collision checks reuse one listing per parent directory instead of rescanning it for every filename.
- The CSV undo log still records only successfully renamed paths. The entire original CLI and v2.1.0 download remain unchanged as fallback.

## Features retained from v2.1.0

- Every proposed rename starts **checked**; untick any row to skip it.
- **Single Select All / Select None button** manages large previews quickly.
- **Edit selected…** (or double-click a row) opens a dialog to customize the proposed filename, including correcting transliteration for personal names.
- Manual names are checked for forbidden Windows characters, duplicate destinations and conflicts with existing files. The app blocks changing a selected parent folder when a proposed descendant rename was explicitly excluded.
- Only checked changes are applied and recorded in the undo log. Preview CSV includes selection/edited status.
- Existing CLI functions, original safety behavior and Windows source-free standalone release remain intact.

## Highlights

- New Windows desktop interface with a folder browser and clear, sortable-free before/after rename table.
- Toggle scanning subdirectories separately from renaming Greek folder names.
- Greek-only name filter; already-Latin filenames remain untouched.
- Safe preview and explicit confirmation before applying any changes.
- Detect and reject an outdated preview if directory contents changed.
- Export the proposed changes to CSV without renaming anything.
- Restore names using the CSV undo log, with exact `UNDO` confirmation.
- Preserve collision protection, filename extensions, recursive scanning safeguards and the original command-line tool.
- Installer-free **Windows EXE** built automatically and smoke-tested on GitHub Actions.
- New professional illustrated-by-layout 10-page PDF user manual.

## Assets

- **Greeklish-Renamer-v2.1.1-Windows-Dimitris-Laidis.zip** — contains `GreeklishRenamer.exe`, PDF, license and quick start; **Python not required**.
- **Greeklish-Renamer-v2.1.1-Source-Dimitris-Laidis.zip** — GUI/CLI Python sources, tests, docs, manual and workflows.
- **Greek_to_Greeklish_Renamer_User_Manual_v2.1.1_Dimitris_Laidis.pdf** — complete standalone manual.

Extract the ZIP first. Review proposed changes and back up important folders independently. The rules are ELOT 743-inspired ASCII transliteration, not certified exact standard conversion. Windows security software may warn about an unsigned new EXE; download only from this repository's official release.

**Repository:** https://github.com/DimitrisLai/Greek-to-greeklish-renamer

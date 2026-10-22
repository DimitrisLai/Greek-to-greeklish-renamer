# Greek to Greeklish Renamer v2.1.0 — Selective Renaming Edition

**Created by Dimitris Laidis · MIT License**

## New in v2.1.0

- Every proposed rename starts **checked**; untick any row to skip it.
- **Select All** and **Select None** let you manage large previews quickly.
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

- **Greeklish-Renamer-v2.1.0-Windows-Dimitris-Laidis.zip** — contains `GreeklishRenamer.exe`, PDF, license and quick start; **Python not required**.
- **Greeklish-Renamer-v2.1.0-Source-Dimitris-Laidis.zip** — GUI/CLI Python sources, tests, docs, manual and workflows.
- **Greek_to_Greeklish_Renamer_User_Manual_v2.1.0_Dimitris_Laidis.pdf** — complete standalone manual.

Extract the ZIP first. Review proposed changes and back up important folders independently. The rules are ELOT 743-inspired ASCII transliteration, not certified exact standard conversion. Windows security software may warn about an unsigned new EXE; download only from this repository's official release.

**Repository:** https://github.com/DimitrisLai/Greek-to-greeklish-renamer

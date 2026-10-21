# Greek to Greeklish Renamer

**A safe Windows desktop app for converting Greek filenames and folder names to Greeklish.**

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
[![MIT License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Python tests](https://github.com/DimitrisLai/Greek-to-greeklish-renamer/actions/workflows/tests.yml/badge.svg)](https://github.com/DimitrisLai/Greek-to-greeklish-renamer/actions/workflows/tests.yml)

**Version 2.0.0 · Created by Dimitris Laidis · MIT License**

## Download

**[Download the latest Windows ZIP, complete source ZIP and professional PDF manual](https://github.com/DimitrisLai/Greek-to-greeklish-renamer/releases/latest)**

The **Windows ZIP** contains `GreeklishRenamer.exe` (no Python required), `README_FIRST.txt`, `LICENSE`, and the user manual. **Extract the ZIP before running the EXE.** The Source ZIP includes the GUI, original CLI, tests and documentation. The app runs locally: no accounts, ads, telemetry, uploads or network lookups.

## Windows desktop interface

- **Choose a directory** with a folder picker, or paste a folder path.
- **Include subdirectories** when needed. Off by default.
- Independently choose whether to **rename Greek folder names**. Disabled unless scanning subdirectories.
- **Only rename names with Greek characters**; English-only or existing Greeklish names are skipped.
- **Preview changes** in a table before committing anything.
- **Export the preview to CSV** without changing files.
- **Apply with confirmation**; reject stale plans when the folder's contents change after Preview.
- Prevent collisions with numbered suffixes such as `(2)` and `(3)`.
- **Undo from CSV** using the log generated during the rename; require exact `UNDO` confirmation.
- Skip symlinks, junctions and Windows reparse points. Preserve file contents.

### First use

1. Download the [v2.0.0 Windows ZIP](https://github.com/DimitrisLai/Greek-to-greeklish-renamer/releases/tag/v2.0.0) and extract it.
2. Double-click **GreeklishRenamer.exe**.
3. Click **Browse…** and choose a small folder to test.
4. Leave subdirectories off initially. Click **Preview changes**.
5. Review the before/after names; click **Apply renames** only when satisfied.
6. Keep the dated undo CSV log in that directory until you verify the results.

**Before large renames, back up important files independently.** Playlists and programs referencing old paths may need updating. Undo is best-effort if paths were moved or changed after a run.

## Examples

| Original filename | New filename |
|---|---|
| Γιώργος Μαζωνάκης.mp3 | Giorgos Mazonakis.mp3 |
| Δημήτρης Κόκοτας.flac | Dimitris Kokotas.flac |
| DJ Set - Ελληνικά.mp3 | DJ Set - Ellinika.mp3 |
| English Song.mp3 | *(unchanged)* |

Transcription uses simplified **ELOT 743 / ISO 843-inspired ASCII** rules, not fully compliant or certified romanization. Familiar spellings of personal names can vary.

## Python source version

Requires Python 3.10+ and the standard library (including Tkinter); no `pip install` is needed to run the application.

```powershell
py greeklish_gui.py                 # Launch the desktop interface
py greeklish_gui.py --self-test     # Noninteractive filesystem smoke test
py rename_greek_to_greeklish.py     # Original interactive CLI
py rename_greek_to_greeklish.py --path "D:\Music" --no-recursive --dry-run
py rename_greek_to_greeklish.py --path "D:\Music" --recursive --files-only
py rename_greek_to_greeklish.py --path "D:\Music" --undo "D:\Music\greeklish_rename_log_...csv"
```

The original `Run_Greek_to_Greeklish.cmd` remains for console users. `Run_Greeklish_Renamer_UI.cmd` launches the GUI from the source edition.

## Testing

```powershell
py -m unittest discover -s tests -v
```

GitHub Actions runs regression tests on **Windows and Linux** using **Python 3.10 and 3.13**. The release workflow builds a Windows EXE using PyInstaller and runs a noninteractive EXE smoke test. A person should still test opening the GUI and renaming a small folder on an actual Windows desktop.

## Documentation and support

- [PDF User Manual — v2.0.0](https://github.com/DimitrisLai/Greek-to-greeklish-renamer/releases/tag/v2.0.0) (included with the Windows ZIP)
- [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [MIT License](LICENSE)
- [Report an issue](https://github.com/DimitrisLai/Greek-to-greeklish-renamer/issues) using fictional filenames and nonsensitive paths

Copyright © 2026 **Dimitris Laidis**. Licensed under the MIT License. Source: [GitHub](https://github.com/DimitrisLai/Greek-to-greeklish-renamer).

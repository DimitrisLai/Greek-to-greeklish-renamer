# Greek to Greeklish Renamer

**Safely convert Greek filenames and folder names into Greeklish.**

**Created by [Dimitris Laidis](https://github.com/DimitrisLai)** · Version **1.2.1** · MIT License

A lightweight command-line utility for Windows and other platforms running Python 3.10+. No additional Python packages are needed to run the application.

## Download

**[Latest GitHub Release — Windows ZIP, Source ZIP & PDF User Manual](https://github.com/DimitrisLai/Greek-to-greeklish-renamer/releases/latest)**

- **Windows ZIP**: the Python script, double-click launcher, license, author credit and public PDF manual.
- **PDF User Manual**: clean 4-page instructions covering folder selection, subdirectories, examples, safe renaming, undo and troubleshooting.
- **Source ZIP**: source code, documentation, tests and license.
- The manual is also kept under [docs](docs/) in this repository after the release build completes.

> Extract the ZIP before running the Windows launcher. Python 3.10 or later must be installed.

## What the application does

- Prompts you to choose a directory when it starts (press Enter for the script's own folder).
- Asks whether to include subdirectories; the default is **No**.
- **Only touches names containing Greek characters.** English/Greeklish-only filenames remain unchanged.
- Optionally converts Greek folder names when scanning subdirectories.
- Shows a full preview and requires you to type **YES** before applying changes.
- Avoids overwriting other files: filename conflicts get suffixes such as \`(2)\` or \`(3)\`.
- Skips symbolic links and Windows junction/reparse points.
- Logs completed changes in a CSV to support undo; changes are to **names**, never file contents.

| Original name | Result |
| --- | --- |
| Γιώργος Μαζωνάκης.mp3 | Giorgos Mazonakis.mp3 |
| Δημήτρης Κόκοτας.flac | Dimitris Kokotas.flac |
| DJ Set - Ελληνικά.mp3 | DJ Set - Ellinika.mp3 |
| English Song.mp3 | Unchanged |

*Note:* The conversion uses simplified ELOT 743 / ISO 843-inspired ASCII rules. It is **not** exact or certified standard-compliant transliteration.

## How to run

1. Extract the Windows ZIP and keep the two program files together.
2. Double-click \`Run_Greek_to_Greeklish.cmd\`.
3. Enter the directory you want to process.
4. Answer the subdirectory question.
5. Review the changes and type \`YES\` to proceed.

You can also use Python directly:

\`\`\`powershell
py rename_greek_to_greeklish.py
py rename_greek_to_greeklish.py --path "D:\Music" --no-recursive --dry-run
py rename_greek_to_greeklish.py --path "D:\Music" --recursive
py rename_greek_to_greeklish.py --path "D:\Music" --recursive --files-only
\`\`\`

### Undo changes

Keep the CSV created in the selected folder, then run:

\`\`\`powershell
py rename_greek_to_greeklish.py --path "D:\Music" --undo "D:\Music\greeklish_rename_log_...csv"
\`\`\`

Type \`UNDO\` when prompted. Missing or conflicting paths are skipped rather than overwritten. Back up important folders before bulk renaming: playlists and applications may still refer to old paths.

## Automated testing

\`\`\`powershell
py -m unittest discover -s tests -v
\`\`\`

The automated suite covers Windows Unicode output, transliteration, Greek-only filtering, folder selection, recursive and nonrecursive scanning, filename conflicts, safety and undo. GitHub Actions runs checks on Windows and Linux.

## Documentation, author and license

- **Public user manual:** attached to [GitHub Releases](https://github.com/DimitrisLai/Greek-to-greeklish-renamer/releases).
- [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md) · [License](LICENSE)
- **Author:** Dimitris Laidis ([DimitrisLai](https://github.com/DimitrisLai))
- **License:** MIT, copyright © 2026 Dimitris Laidis.

Greek romanization references: [ELOT](https://eshop.elot.gr/en/product/70972), [Greek Passport Authority](https://passport.gov.gr/passports/GrElotConverter/GrElotConverterEn.html).

# Greek to Greeklish Renamer

**Safely rename Greek filenames and folders to Greeklish.**

**Created by Dimitris Laidis** ([DimitrisLai](https://github.com/DimitrisLai))  
Python 3.10+ · No third-party packages · Windows launcher included.

## Features

- Asks for target directory at startup. Enter uses the folder containing the script.
- Asks whether to scan subdirectories and rename Greek folder names.
- **Skips all filenames without Greek characters**.
- Previews every planned change and requires typing YES before applying.
- Avoids overwrites by adding (2), (3), etc.
- Keeps file contents untouched and writes a CSV undo log.
- Skips symbolic links and Windows junction/reparse points.

**Greek transcription:** ELOT 743 / ISO 843-inspired ASCII transcription; accents removed and some contextual rules simplified. Not a certified exact implementation.

| Before | After |
| --- | --- |
| Γιώργος Μαζωνάκης.mp3 | Giorgos Mazonakis.mp3 |
| Δημήτρης Κόκοτας.flac | Dimitris Kokotas.flac |
| DJ Mix - Ελληνικά.mp3 | DJ Mix - Ellinika.mp3 |
| English Song.mp3 | Unchanged |

## Windows quick start

1. Put rename_greek_to_greeklish.py and Run_Greek_to_Greeklish.cmd together.
2. Double-click Run_Greek_to_Greeklish.cmd.
3. Enter a folder path or press Enter for the launcher folder.
4. Choose Y or N for subdirectories.
5. Review the preview; enter YES to rename or anything else to cancel.

Make a backup before bulk changes, especially when playlists or software refer to old filenames.

## Command line

    py rename_greek_to_greeklish.py
    py rename_greek_to_greeklish.py --path "D:\Music" --no-recursive --dry-run
    py rename_greek_to_greeklish.py --path "D:\Music" --recursive
    py rename_greek_to_greeklish.py --path "D:\Music" --recursive --files-only
    py rename_greek_to_greeklish.py --path "D:\Music" --undo "D:\Music\greeklish_rename_log_YYYYMMDD_HHMMSS_microseconds.csv"

## Tests

    python -m unittest discover -s tests -v

## License and publishing

MIT licensed, copyright © 2026 Dimitris Laidis. See LICENSE and docs/PUBLISHING.md.

A public PDF user manual is included in the downloadable release ZIP.

References: [ELOT](https://eshop.elot.gr/en/product/70972), [Greek Passport Authority](https://passport.gov.gr/passports/GrElotConverter/GrElotConverterEn.html).

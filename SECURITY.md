# Security and data safety

Greek to Greeklish Renamer is a local Python utility that renames files and folders in a directory selected by the user. It does not upload filenames or file contents to an external service, and the application requires no third-party Python packages.

## Safer use

- Always inspect the preview. Renaming starts only when you type the exact confirmation **YES**.
- Test with a small folder before running on a large collection, and keep an independent backup of important files.
- Only names containing Greek characters are candidates for renaming; file contents are not intentionally modified.
- The application skips symbolic links and Windows junctions/reparse points when scanning.
- If a destination is occupied, the renamer generates an available name such as `Song (2).mp3` rather than overwriting it.
- A CSV undo log records completed changes. Undo is not a substitute for a separate backup: concurrent changes, permissions, moved files, filesystem failures or unexpected interruptions can make restoration incomplete.
- Renaming can break existing links from playlists, applications or shortcuts to old file paths.

## Reporting a vulnerability

For a **security vulnerability**, prefer GitHub's private vulnerability reporting option on the repository's **Security** tab *if it is enabled*. If private reporting is unavailable, open a GitHub issue containing only nonsensitive information to ask for a private contact method. Do not publicly post exploit details, private directory paths or personal filenames.

For ordinary bugs, open a GitHub Issue with invented filenames, expected and actual results, the Python version and operating system. Never upload private file listings, music libraries or credentials.

## Scope

Supported release: **v1.2.1**. As with any bulk file operation, review the changes and keep backups; automated tests cannot cover every filesystem or Windows configuration.

Created by **Dimitris Laidis**. MIT License — see [LICENSE](LICENSE).

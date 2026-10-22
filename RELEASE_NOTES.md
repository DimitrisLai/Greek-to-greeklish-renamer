# Greek to Greeklish Renamer v2.4.0 — Remembered Settings & Cancel Scan

**Dimitris Laidis · MIT License**

### What's new

- Remembers the last existing, valid folder and file-type selection (including custom extension text) in a local, atomic settings file. The app does **not** scan or rename automatically when relaunched.
- New **Cancel scan** button during read-only preview scans. Cooperative cancellation discards the partial scan and changes no filenames. Closing the window while scanning offers cancellation and keeps the window open until the worker exits.
- Preserves **Stop safely** for renaming, detailed result logs, extension protection, built-in History / confirmed Undo, no-overwrite collision checks and the existing command-line edition.
- Further tests for corrupted settings, symlink/missing last folders, cancellation timing, 400+ file GUI scan acceptance and recovery after cancellation.

### Windows 11 Explorer menu — limitation

The optional **classic** folder menu still works under **Show more options** in Windows 11, with read-only preview and reversible per-user registration. Microsoft requires a **native IExplorerCommand DLL plus a signed sparse/MSIX package** for the **modern, top-level** Windows 11 menu. That signed shell extension has **not yet been built, installed or validated**, so v2.4.0 **does not claim modern-menu support**. See `docs/WINDOWS_11_MODERN_MENU.md` for requirements. SignPath Foundation code-signing approval is independent and still pending confirmation.

### Separate downloads

- `Greeklish-Renamer-v2.4.0-Windows-Dimitris-Laidis.zip` — standalone Windows EXE + PDF.
- `Greeklish-Renamer-v2.4.0-Source-Dimitris-Laidis.zip` — complete source and tests.
- `Greek_to_Greeklish_Renamer_User_Manual_v2.4.0_Dimitris_Laidis.pdf` — professional 10-page guide.
- `SHA256SUMS.txt` — SHA-256 checksums for Windows ZIP, Source ZIP and PDF.

**Security:** No external servers, telemetry, automatic renaming or unsupervised filesystem changes; always test on backups. This release is not digitally signed until signing is approved.

Repository: https://github.com/DimitrisLai/Greek-to-greeklish-renamer

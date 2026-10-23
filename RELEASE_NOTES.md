# Greek to Greeklish Renamer v2.5.0 — Black Theme & Release Polish

**Dimitris Laidis · MIT License**

### What's new

- **Black theme** with a one-click **Black theme / Light theme** switch.
- Theme covers the complete main window, preview rows and checkbox icons, history and results dialogs.
- Appearance choice is persisted locally in the existing settings file. Previous installations default safely to Light.
- Theme changes do not clear or recompute previews, alter selections, or perform any renames.
- Additional contrast/persistence tests and real Tkinter GUI smoke coverage on Linux with Xvfb.
- Existing core behaviors remain unchanged: previews, custom edits, extension protection, cancellation, safe stop, history, collision prevention and CSV undo.
- Tested rename workloads include a user-reported successful batch of over 1,700 filenames; this is one user's experience, not an independent compatibility guarantee.

### Downloads

- `Greeklish-Renamer-v2.5.0-Windows-Dimitris-Laidis.zip` — standalone Windows EXE, guide and license.
- `Greeklish-Renamer-v2.5.0-Source-Dimitris-Laidis.zip` — source code and automated tests.
- `Greek_to_Greeklish_Renamer_User_Manual_v2.5.0_Dimitris_Laidis.pdf` — printable user manual.
- `SHA256SUMS.txt` — SHA-256 hashes.

### Known limitation

On Windows 11 the optional Explorer integration still uses the classic right-click menu under **Show more options**. A modern top-level extension is not included.

**Code signing:** The EXE is currently **unsigned** while the SignPath Foundation application is being reviewed. Verify official GitHub release files and SHA-256 checksums, and do not bypass Windows security warnings.

Repository: https://github.com/DimitrisLai/Greek-to-greeklish-renamer

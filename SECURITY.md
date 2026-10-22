# Security and data safety

Greek to Greeklish Renamer is a local filename-renaming utility. It never reads media contents for transformation and does not upload filenames or contents, contact external servers, add telemetry, or require a user account.

## Recommendations

- Always inspect the preview first. Never run bulk renames without an independent backup.
- Options changed after preview invalidate the plan; just before applying, the filesystem is rescanned to reject stale plans.
- Existing Latin names are protected by numbered suffixes on collisions.
- Symbolic links, junctions and reparse points are skipped during recursive scans.
- CSV undo can restore completed changes in reverse order, but is not a substitute for a backup: external moves, interrupted writes, permissions and unusual filesystems can prevent complete recovery.
- Renaming filenames or directories may break external references such as playlists.

## Optional Explorer integration

The Windows Explorer folder right-click command is **not installed automatically**. A user must explicitly open the standalone EXE, choose **Explorer menu…** and approve installation. Registration modifies only `HKEY_CURRENT_USER\Software\Classes\Directory` menu entries created for this application; it needs no elevation and can be removed through the same window. The command only selects the folder and generates a read-only preview. It never supplies CLI `--yes` or automatically applies changes. After moving the EXE, remove or update the menu.

## Reporting security concerns

Use GitHub private vulnerability reporting from the **Security** tab if enabled. Otherwise open a nonsensitive issue asking for a private contact channel. Never publish private directory listings, exploit details, passwords or other people's data.

For ordinary bugs, open an [Issue](https://github.com/DimitrisLai/Greek-to-greeklish-renamer/issues) with fictional names and your Windows/Python version.

Current public release: v2.2.0. Licensed under [MIT](LICENSE). © 2026 Dimitris Laidis.

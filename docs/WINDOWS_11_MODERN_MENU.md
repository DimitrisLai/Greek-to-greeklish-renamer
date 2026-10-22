# Windows 11 modern Explorer context menu — technical status

**Status for v2.4.0: NOT YET INSTALLED / NOT SHIPPED.** The existing opt-in classic right-click command remains supported on Windows 10 and under **Show more options** on Windows 11. It opens a **read-only preview only**.

A modern top-level Windows 11 command is **not** equivalent to setting another registry key. Microsoft's official design requires:

1. A native **x64 IExplorerCommand COM DLL** whose menu-construction methods are fast and read-only.
2. A `windows.comServer` and `windows.fileExplorerContextMenus` package manifest registration, scoped to **Directory** (and optionally **Directory\\Background**).
3. A signed MSIX/sparse-package identity that loads the COM handler from an appropriate architecture and lets the `Invoke` method launch only the safe `GreeklishRenamer.exe --folder <selected directory>` path.
4. Signed-package installation and removal, rollback, trust, architecture, and Windows 11 Explorer tests before distributing to users.

The v2.4.0 standalone portable EXE does not currently have that package identity. The requested SignPath Foundation application is separate and remains pending until confirmed. Never install an unsigned native shell handler into Explorer or pretend the classic registry verb is a modern context-menu extension.

Official references:
- https://learn.microsoft.com/en-us/windows/apps/desktop/modernize/integrate-packaged-app-with-file-explorer
- https://learn.microsoft.com/en-us/windows/apps/desktop/modernize/grant-identity-to-nonpackaged-apps
- https://microsoft.github.io/PowerToys/common/context-menus/

**Acceptance criteria before release:** a signed package installed successfully on a real Windows 11 machine, top-level context-menu visibility, no rename without preview/confirmation, no Explorer slowdown/crash, clean uninstallation and no duplicate classic entries.

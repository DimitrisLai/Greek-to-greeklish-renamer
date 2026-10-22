# Publishing Windows Desktop Edition

This repository automatically tests Python 3.10 and 3.13 on Windows and Linux via `.github/workflows/tests.yml`.

The one-time **v2.1.2** release workflow `.github/workflows/release-v2.1.2.yml` builds a native Windows EXE with PyInstaller on Windows, tests the EXE via `--self-test`, generates a 10-page PDF on Linux, then publishes the ZIPs and PDF into the GitHub Release. It also publishes a copy of the PDF to `docs/` on `main`.

## Public release assets

- `Greeklish-Renamer-v2.1.2-Windows-Dimitris-Laidis.zip` — EXE + PDF + license + README_FIRST.
- `Greeklish-Renamer-v2.1.2-Source-Dimitris-Laidis.zip` — sources + tests + docs + PDF.
- `Greek_to_Greeklish_Renamer_User_Manual_v2.1.2_Dimitris_Laidis.pdf` — public manual.

## Prepare any future version

Update the version in Python files, changelog, README, release notes, PDF generator, build script, Windows launchers and release workflow. Create an **independent new release workflow** for a new tag, or convert this single-version workflow to an explicitly parameterized one. Do **not** overwrite an existing historical release tag as if it were a new version.

The application has no runtime pip dependencies. `reportlab`, `pypdf` and `pyinstaller` are **build-only** tools. GitHub user-facing topics are configured in repository settings.

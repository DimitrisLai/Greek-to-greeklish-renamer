# Contributing

Thank you for contributing to Greek to Greeklish Renamer by Dimitris Laidis.

- File issues with **fictional filenames** and the expected/actual spellings. Never publish personal directory paths or entire music libraries.
- Preserve all safety rules: no overwriting unrelated names, preview-before-apply, Greek-only filter, collision-safe suffixes and undo logs.
- Keep Python 3.10+ compatibility and the standard-library-only runtime (Tkinter for GUI).
- GUI service operations belong in `renamer_service.py`; keep UI interactions on the Tk thread.
- Add regression tests for each bug and run `python -m unittest discover -s tests -v` before a PR.
- Test both the original CLI and new GUI; smoke-test the bundled Windows EXE when possible.

Project license: [MIT](LICENSE).

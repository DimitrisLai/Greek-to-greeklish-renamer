# Publishing and maintenance

**Project:** https://github.com/DimitrisLai/Greek-to-greeklish-renamer

**Author:** Dimitris Laidis

## Public release

The repository includes a one-time GitHub Actions workflow under `.github/workflows/publish-v1.2.1.yml`. The workflow:

1. Tests the Python application on Ubuntu.
2. Generates the four-page public PDF user manual.
3. Builds the Windows ZIP and source ZIP.
4. Creates the v1.2.1 GitHub Release or replaces existing release assets.
5. Publishes downloadable ZIP and PDF assets to GitHub Releases. The current manual is also archived in `docs/`.

The release includes three assets: the Windows ZIP, the source ZIP, and the user manual PDF.

The source ZIP is **not** a compiled executable: users need Python 3.10+ to run the program.

## Search topics

`greeklish`, `greek`, `transliteration`, `elot-743`, `python`, `file-renamer`, `batch-rename`, `windows`, `unicode`, `cli`.

Repository Topics require owner/admin settings access. Add them manually with the gear icon in the repository's **About** section. The automatic workflow does not change repository Topics.

## Future releases

For maintenance, use v1.2.1 for fixes, v1.3.0 for compatible feature additions, and v2.0.0 for breaking changes. Update versions in the Python script, manual generator, build script, release workflow, README and changelog.

## Testing

Run `python -m unittest discover -s tests -v` locally. Ensure GitHub Actions checks pass before tagging the next public version.

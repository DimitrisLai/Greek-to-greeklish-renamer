# Publishing Greek to Greeklish Renamer v2.3.0

The v2.3.0 GitHub Actions workflow runs cross-platform unit tests, builds a Windows EXE with icon and Windows version information, exercises its headless filesystem smoke test, generates a 10-page PDF, validates the three release archives and publishes `SHA256SUMS.txt` with checksums for the Windows ZIP, Source ZIP and PDF.

Explorer registry changes are user-controlled and are never executed in CI or during extraction. Runtime Python needs no third-party dependencies. The project remains unsigned unless SignPath Foundation separately approves signing.

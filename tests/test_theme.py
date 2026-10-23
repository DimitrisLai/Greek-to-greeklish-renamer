"""Black-theme regression tests that do not require a graphical desktop."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from theme_support import THEMES, translated
from user_preferences import Preferences, load, save, sanitize


class ThemeSettingsTests(unittest.TestCase):
    def test_modes_are_exact(self):
        self.assertEqual(THEMES, ("Light", "Black"))

    def test_black_theme_survives_restart(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "settings.json"
            expected = Preferences(str(root), "MP3 only", ".mp3", "Black")
            self.assertTrue(save(expected, path))
            restored = load(path)
            self.assertEqual(restored.appearance, "Black")
            self.assertEqual(restored.file_type_preset, "MP3 only")
            self.assertEqual(restored.last_folder, str(root.resolve()))

    def test_old_settings_default_to_light(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "settings.json"
            path.write_text(json.dumps({"schema_version": 1, "last_folder": str(root),
                                        "file_type_preset": "WAV only",
                                        "custom_file_types": ".wav"}), encoding="utf-8")
            restored = load(path)
            self.assertEqual(restored.appearance, "Light")
            self.assertEqual(restored.file_type_preset, "WAV only")

    def test_unexpected_mode_is_rejected(self):
        for bad in ("system", "Dark", "black", "", None, 1, [], {}):
            with self.subTest(bad=bad):
                self.assertEqual(sanitize({"appearance": bad}).appearance, "Light")

    def test_light_and_black_colors_have_contrast_roles(self):
        self.assertEqual(translated("foreground", "#FFFFFF", True), "#ffffff")
        self.assertNotEqual(translated("background", "#FFFFFF", True), "#ffffff")
        self.assertNotEqual(translated("foreground", "#101E32", True), "#101E32")
        self.assertEqual(translated("background", "#FFFFFF", False), "#FFFFFF")

    def test_disabled_visual_state_is_not_renamer_state(self):
        self.assertEqual(translated("state", "disabled", True), "disabled")
        self.assertEqual(translated("command", "safe", True), "safe")


if __name__ == "__main__":
    unittest.main()

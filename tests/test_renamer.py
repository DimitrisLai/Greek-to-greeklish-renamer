import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "rename_greek_to_greeklish.py"
spec = importlib.util.spec_from_file_location("renamer", SCRIPT)
ren = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ren)

class TransliterationTests(unittest.TestCase):
    def test_names(self):
        examples = {
            "Γιώργος Μαζωνάκης": "Giorgos Mazonakis",
            "Δημήτρης Κόκοτας": "Dimitris Kokotas",
            "Χρήστος": "Christos",
            "Μπάμπης": "Bampis",
            "Αυτοκίνητο": "Aftokinito",
            "Ευτυχία": "Eftychia",
            "DJ - Ελληνικά": "DJ - Ellinika",
        }
        for original, expected in examples.items():
            with self.subTest(original=original):
                self.assertEqual(ren.to_greeklish(original), expected)

    def test_greek_detection(self):
        self.assertTrue(ren.contains_greek_letters("Μουσική.mp3"))
        self.assertTrue(ren.contains_greek_letters("DJ - Τραγούδι.mp3"))
        self.assertFalse(ren.contains_greek_letters("English.mp3"))

    def test_collision(self):
        self.assertEqual(ren.available_name("Ellinika.mp3", {"ellinika.mp3"}, False), "Ellinika (2).mp3")

    def test_case_and_extension(self):
        self.assertEqual(ren.converted_name("Μουσική.FLAC", False), "Mousiki.FLAC")

class FilesystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def put(self, relative, data=b"original"):
        path = self.root / relative
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_bytes(data)
        return path

    def test_nonrecursive(self):
        self.put("Ελληνικά.mp3")
        self.put("folder/Τραγούδι.mp3")
        self.put("English.mp3")
        plan = ren.plan_renames(self.root, recursive=False)
        self.assertEqual(len(plan), 1)
        count, log = ren.apply_plan(self.root, plan)
        self.assertEqual(count, 1)
        self.assertTrue((self.root / "folder/Τραγούδι.mp3").exists())
        self.assertEqual((self.root / "Ellinika.mp3").read_bytes(), b"original")
        self.assertEqual(ren.undo(self.root, log, confirmed=True), (1, 1))

    def test_recursive_undo(self):
        self.put("Ελληνικά/Τραγούδι.mp3")
        plan = ren.plan_renames(self.root, recursive=True)
        self.assertEqual(len(plan), 2)
        count, log = ren.apply_plan(self.root, plan)
        self.assertEqual(count, 2)
        self.assertTrue((self.root / "Ellinika/Tragoudi.mp3").exists())
        self.assertEqual(ren.plan_renames(self.root, recursive=True), [])
        self.assertEqual(ren.undo(self.root, log, confirmed=True), (2, 2))
        self.assertTrue((self.root / "Ελληνικά/Τραγούδι.mp3").exists())

    def test_latin_collision(self):
        self.put("Ελληνικά.mp3")
        self.put("Ellinika.mp3", b"KEEP")
        plan = ren.plan_renames(self.root)
        self.assertEqual(plan[0][1].name, "Ellinika (2).mp3")
        ren.apply_plan(self.root, plan)
        self.assertEqual((self.root / "Ellinika.mp3").read_bytes(), b"KEEP")

    def test_symlink_directory_excluded(self):
        outside = self.root / "English"
        self.put("English/Ελληνικά.mp3")
        try:
            (self.root / "Σύνδεσμος").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Directory symlinks unavailable")
        plan = ren.plan_renames(self.root, recursive=True)
        self.assertEqual(len(plan), 1)
        self.assertTrue(all("Σύνδεσμος" not in str(a) for a,b in plan))

if __name__ == "__main__":
    unittest.main()

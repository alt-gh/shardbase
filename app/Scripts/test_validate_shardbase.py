import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_shardbase import validate_database


VALID_DATABASE = Path(__file__).parent / "fixtures" / "valid-database"


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "app" / "Knowledge" / "Databases" / "Example Database"
        self.database.parent.mkdir(parents=True)
        shutil.copytree(VALID_DATABASE, self.database)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_database_passes(self):
        self.assertEqual(validate_database(self.database), [])

    def test_missing_manifest_field_is_reported(self):
        manifest = self.database / "Database.md"
        manifest.write_text(manifest.read_text().replace("database_status: active\n", ""), encoding="utf-8")
        codes = {issue.code for issue in validate_database(self.database)}
        self.assertIn("manifest-field", codes)

    def test_note_without_frontmatter_is_reported(self):
        note = self.database / "Data" / "Game" / "Unstructured.md"
        note.write_text("# Unstructured\n\nThis must not be silently ignored.\n", encoding="utf-8")
        codes = {issue.code for issue in validate_database(self.database)}
        self.assertIn("structural-frontmatter", codes)

    def test_pebble_cannot_parent_a_note(self):
        shard = self.database / "Data" / "Game" / "Example - Weapons.md"
        shard.write_text(shard.read_text(encoding="utf-8").replace("parent_note: \"[[Example]]\"", "parent_note: \"[[Example - Weapons - Blade]]\""), encoding="utf-8")
        codes = {issue.code for issue in validate_database(self.database)}
        self.assertIn("pebble-parent", codes)

    def test_lineage_cycle_is_reported(self):
        first = self.database / "Data" / "Game" / "Example - Weapons.md"
        first.write_text(first.read_text(encoding="utf-8").replace("parent_note: \"[[Example]]\"", "parent_note: \"[[Example - Weapons - Blade]]\""), encoding="utf-8")
        codes = {issue.code for issue in validate_database(self.database)}
        self.assertIn("lineage-cycle", codes)

    def test_unbounded_filename_is_reported(self):
        source = self.database / "Data" / "Game" / "Example - Weapons - Blade.md"
        target = source.with_name("Example - Weapons - Blade - Extra.md")
        source.rename(target)
        codes = {issue.code for issue in validate_database(self.database)}
        self.assertIn("filename-context", codes)

if __name__ == "__main__":
    unittest.main()

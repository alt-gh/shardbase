"""Bootstrap proofs use disposable instances and synthetic data only."""

import contextlib
import io
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote

import yaml

from database_creation import available_blueprints, create_database, rebase_framework_links
from note_creation import CreationError
from shardbase import main
from validate_shardbase import parse_frontmatter, validate_database


SCRIPTS = Path(__file__).resolve().parent
BLUEPRINT = SCRIPTS.parent / "Blueprints/Games"


class DatabaseCreationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "Example Instance"
        self.source = self.root / "app/Blueprints/Games"
        shutil.copytree(BLUEPRINT, self.source)
        (self.root / "app/Docs").mkdir()
        (self.root / "app/Docs/Shard System Specification.md").write_text("Framework specification placeholder\n")
        (self.root / "app/Scripts").mkdir()
        (self.root / "app/Scripts/README.md").write_text("Framework tooling placeholder\n")
        self.destination = self.root / "app/Knowledge/Databases/Games"

    def snapshot(self, directory):
        return {path.relative_to(directory): path.read_bytes() for path in directory.rglob("*") if path.is_file() and not path.is_symlink()}

    def update_manifest(self, path, **fields):
        metadata, body = parse_frontmatter(path.read_text())
        metadata.update(fields)
        path.write_text("---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n" + body)

    def run_cli(self, *args, **kwargs):
        return subprocess.run([sys.executable, "-B", str(SCRIPTS / "shardbase.py"), *args],
                              input="", text=True, capture_output=True, cwd=self.root, **kwargs)

    def test_bootstrap_copies_resources_and_empty_directories_and_preserves_source(self):
        before = self.snapshot(self.source)
        (self.source / "Views/Empty").mkdir()
        result = create_database(self.root, "games")
        self.assertEqual(result, self.destination)
        self.assertEqual(before, self.snapshot(self.source))
        self.assertEqual(validate_database(result), [])
        self.assertTrue((result / "Data/Game/Attachments").is_dir())
        self.assertTrue((result / "Views/Empty").is_dir())
        self.assertTrue((self.root / "app/Knowledge/Inbox").is_dir())
        self.assertEqual(set(before), set(self.snapshot(result)))
        for path, contents in before.items():
            if path not in (Path("Database.md"), Path("Agents/Vera.md")):
                self.assertEqual((result / path).read_bytes(), contents)

    def test_framework_and_internal_markdown_links_resolve_in_new_database(self):
        result = create_database(self.root, "games")
        for relative in ("Database.md", "Agents/Vera.md"):
            note = result / relative
            targets = re.findall(r"\]\(([^\s)]+)\)", note.read_text())
            self.assertTrue(targets)
            for target in targets:
                self.assertTrue((note.parent / unquote(target)).is_file(), (relative, target))
        self.assertIn("../../../Docs/", (result / "Database.md").read_text())
        self.assertIn("../../../../Docs/", (result / "Agents/Vera.md").read_text())

    def test_rebasing_preserves_code_local_links_and_external_urls(self):
        original = self.source / "Database.md"
        text = (
            "[Spec](../../Docs/Shard%20System%20Specification.md#structure)\n"
            "[Local](Templates/Game.md)\n[Web](https://example.com/guide)\n"
            "`[Code](../../Docs/Shard%20System%20Specification.md)`\n"
            "```markdown\n[Code](../../Docs/Shard%20System%20Specification.md)\n```\n"
        )
        expected = text.replace("[Spec](../../Docs/", "[Spec](../../../Docs/", 1)
        self.assertEqual(rebase_framework_links(text, self.root, original, self.destination / "Database.md"), expected)

    def test_added_blueprint_is_discovered_without_games_specific_code(self):
        extra = self.source.with_name("Example Library")
        shutil.copytree(SCRIPTS / "fixtures/valid-database", extra)
        self.update_manifest(extra / "Database.md", database_id="example-library", database_name="Example Library")
        options = available_blueprints(self.root)
        self.assertEqual({item.database_id for item in options}, {"games", "example-library"})
        result = create_database(self.root, "example-library")
        self.assertEqual(result.name, "Example Library")
        self.assertEqual(validate_database(result), [])
        self.assertFalse(self.destination.exists())

    def test_existing_database_and_user_edits_are_never_replaced(self):
        create_database(self.root, "games")
        user = self.destination / "Templates/Game.md"
        user.write_text(user.read_text() + "\nUser-authored content\n")
        before = self.snapshot(self.root)
        with self.assertRaisesRegex(CreationError, "already uses"):
            create_database(self.root, "games")
        self.assertEqual(before, self.snapshot(self.root))

    def test_duplicate_identity_under_another_folder_is_refused(self):
        create_database(self.root, "games").rename(self.destination.with_name("My Library"))
        before = self.snapshot(self.root)
        with self.assertRaisesRegex(CreationError, "already declares database_id"):
            create_database(self.root, "games")
        self.assertEqual(before, self.snapshot(self.root))
        self.assertFalse(self.destination.exists())

    def test_case_insensitive_destination_collision_is_refused(self):
        other = self.destination.with_name("gAmEs")
        other.mkdir(parents=True)
        with self.assertRaisesRegex(CreationError, "already uses"):
            create_database(self.root, "games")
        self.assertEqual(list(other.iterdir()), [])

    def test_duplicate_blueprint_identity_is_refused(self):
        shutil.copytree(self.source, self.source.with_name("Duplicate"))
        with self.assertRaisesRegex(CreationError, "Multiple blueprints"):
            available_blueprints(self.root)
        self.assertFalse((self.root / "app/Knowledge").exists())

    def test_invalid_blueprint_is_validated_before_live_writes(self):
        self.update_manifest(self.source / "Database.md", manifest_version=2)
        with self.assertRaisesRegex(CreationError, "manifest-version"):
            create_database(self.root, "games")
        self.assertFalse((self.root / "app/Knowledge").exists())

    def test_missing_scaffolding_is_reported_before_live_writes(self):
        shutil.rmtree(self.source / "Views")
        with self.assertRaisesRegex(CreationError, "views-missing"):
            create_database(self.root, "games")
        self.assertFalse((self.root / "app/Knowledge").exists())

    def test_missing_and_archived_blueprints_do_not_create_databases(self):
        with self.assertRaisesRegex(CreationError, "No blueprint"):
            create_database(self.root, "missing")
        self.update_manifest(self.source / "Database.md", database_status="archived")
        with self.assertRaisesRegex(CreationError, "active or draft"):
            create_database(self.root, "games")
        self.assertFalse((self.root / "app/Knowledge").exists())

    def test_malformed_source_and_existing_manifests_are_not_guessed(self):
        manifest = self.source / "Database.md"
        original = manifest.read_bytes()
        manifest.write_text("---\ndatabase_id: [unfinished\n")
        with self.assertRaises(CreationError):
            create_database(self.root, "games")
        manifest.write_bytes(original)
        other = self.destination.with_name("Other")
        other.mkdir(parents=True)
        (other / "Database.md").write_text("---\ndatabase_id: [unfinished\n")
        before = self.snapshot(self.root)
        with self.assertRaises(CreationError):
            create_database(self.root, "games")
        self.assertEqual(before, self.snapshot(self.root))

    def test_source_symlink_is_refused_without_reading_external_content(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.source / "Views/External").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(CreationError, "Symlink"):
                create_database(self.root, "games")
            self.assertEqual(list(Path(outside).iterdir()), [])
        self.assertFalse((self.root / "app/Knowledge").exists())

    def test_destination_symlink_is_refused(self):
        with tempfile.TemporaryDirectory() as outside:
            path = self.root / "app/Knowledge"
            path.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(CreationError, "Symlink"):
                create_database(self.root, "games")
            self.assertEqual(list(Path(outside).iterdir()), [])

    def test_generated_runtime_in_blueprint_is_never_copied(self):
        (self.source / ".venv").mkdir()
        with self.assertRaisesRegex(CreationError, "runtime/build"):
            create_database(self.root, "games")
        self.assertFalse((self.root / "app/Knowledge").exists())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO support")
    def test_special_file_is_refused_before_copy(self):
        os.mkfifo(self.source / "Views/Pipe")
        with self.assertRaisesRegex(CreationError, "ordinary files"):
            create_database(self.root, "games")

    def test_temporary_directory_must_be_external(self):
        with patch("database_creation.tempfile.gettempdir", return_value=str(self.root)):
            with self.assertRaisesRegex(CreationError, "temporary directory"):
                create_database(self.root, "games")
        self.assertFalse((self.root / "app/Knowledge").exists())

    def test_failed_final_copy_reports_partial_state_without_deleting_it(self):
        before = self.snapshot(self.source)
        with patch("database_creation.copy_new_file", side_effect=OSError("Simulated disk failure")):
            with self.assertRaisesRegex(CreationError, "partial new folder"):
                create_database(self.root, "games")
        self.assertTrue(self.destination.is_dir())
        self.assertEqual(before, self.snapshot(self.source))
        with self.assertRaisesRegex(CreationError, "already uses"):
            create_database(self.root, "games")

    def test_interactive_single_blueprint_still_offers_a_choice(self):
        with patch("builtins.input", return_value="1") as choice, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["create", "new", "database", "--root", str(self.root)]), 0)
        choice.assert_called_once()
        self.assertIn("Games", output.getvalue())
        self.assertIn("Database created", output.getvalue())
        self.assertEqual(validate_database(self.destination), [])

    def test_cancelled_selection_and_empty_catalog_write_nothing(self):
        with patch("builtins.input", side_effect=KeyboardInterrupt()), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["create", "new", "database", "--root", str(self.root)]), 130)
        shutil.rmtree(self.source)
        result = self.run_cli("create", "new", "database", "--root", str(self.root))
        self.assertEqual(result.returncode, 1)
        self.assertIn("No blueprints", result.stderr)
        self.assertFalse((self.root / "app/Knowledge").exists())

    def test_note_options_are_not_silently_ignored_for_database_creation(self):
        result = self.run_cli("create", "new", "--title", "Example", "database", "--blueprint", "games", "--root", str(self.root))
        self.assertEqual(result.returncode, 1)
        self.assertIn("Note options", result.stderr)
        self.assertFalse(self.destination.exists())

    def test_subprocess_bootstrap_to_note_creation_and_validation(self):
        result = self.run_cli("create", "new", "--root", str(self.root), "database", "--blueprint", "games", "--no-color")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.destination / "Agents/Vera.md").is_file())
        note = self.run_cli("create", "new", "--root", str(self.root), "--title", "Example Game", "--type", "core",
                            "--alias", "", "--intent", "database", "--database", "games")
        self.assertEqual(note.returncode, 0, note.stderr)
        draft = self.root / "app/Knowledge/Inbox/Example Game.md"
        original = draft.read_bytes()
        promoted = self.destination / "Data/Game/Example Game.md"
        shutil.move(draft, promoted)
        validation = self.run_cli("validate", "--root", str(self.root))
        self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
        self.assertEqual(original, promoted.read_bytes())
        self.assertEqual(list(self.root.rglob("__pycache__")), [])


if __name__ == "__main__":
    unittest.main()

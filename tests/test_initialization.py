"""Guided initialization orchestration and preservation boundaries."""

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _support import GAMES_BLUEPRINT, ROOT

# _support makes the non-packaged scripts importable.
# isort: split
import initialization
import shardbase
from backup_restore import BackupError, backup
from doctor import CheckResult
from validate_shardbase import Issue

PASSWORD = b"synthetic passphrase"


class FakeUI:
    def __init__(self, *answers):
        self.answers = list(answers)
        self.sections = []

    def section(self, title):
        self.sections.append(title)

    def choose(self, title, choices):
        self.sections.append(title)
        answer = self.answers.pop(0)
        self.assert_choice(answer, choices)
        return answer

    @staticmethod
    def assert_choice(answer, choices):
        if answer not in {choice[0] for choice in choices}:
            raise AssertionError(f"{answer!r} was not an offered choice")


class InitializationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "Example Instance"
        self.root.mkdir()
        shutil.copytree(GAMES_BLUEPRINT, self.root / "app/Blueprints/Games")
        specification = self.root / "app/Docs/Shard System Specification.md"
        specification.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "app/Docs/Shard System Specification.md", specification)

    def run_new(self, ui=None):
        output = io.StringIO()
        with patch.object(initialization, "preflight", return_value=True), \
                patch("doctor.diagnose", return_value=[]), contextlib.redirect_stdout(output):
            status = initialization.initialize_new_instance(self.root, ui or FakeUI("games"))
        return status, output.getvalue()

    def test_fresh_new_instance_delegates_creation_and_verifies_without_first_note(self):
        self.assertFalse((self.root / "app/Knowledge").exists())
        status, output = self.run_new()
        database = self.root / "app/Knowledge/Databases/Games"
        self.assertEqual(status, 0, output)
        self.assertTrue((self.root / "app/Knowledge/Inbox").is_dir())
        self.assertTrue((database / "Database.md").is_file())
        self.assertEqual(list((database / "Data/Game").rglob("*.md")), [])
        self.assertIn("Structural validation passed", output)
        self.assertIn("shardbase create new", output)
        self.assertIn("Database-semantic validity is not fully automated", output)

    def test_existing_database_is_filtered_and_all_materialized_exits_unchanged(self):
        self.assertEqual(self.run_new()[0], 0)
        database = self.root / "app/Knowledge/Databases/Games"
        before = {path.relative_to(database): path.read_bytes() for path in database.rglob("*") if path.is_file()}
        status, output = self.run_new(FakeUI())
        self.assertEqual(status, 0)
        self.assertIn("No additional supplied blueprint", output)
        self.assertEqual(before, {path.relative_to(database): path.read_bytes() for path in database.rglob("*") if path.is_file()})

    def test_unused_blueprint_remains_selectable_beside_existing_database(self):
        self.assertEqual(self.run_new()[0], 0)
        movies = self.root / "app/Blueprints/Movies"
        shutil.copytree(GAMES_BLUEPRINT, movies)
        manifest = movies / "Database.md"
        text = manifest.read_text(encoding="utf-8")
        text = text.replace("database_id: games", "database_id: movies", 1)
        text = text.replace("database_name: Games", "database_name: Movies", 1)
        manifest.write_text(text, encoding="utf-8")
        status, output = self.run_new(FakeUI("movies"))
        self.assertEqual(status, 0, output)
        self.assertTrue((self.root / "app/Knowledge/Databases/Movies/Database.md").is_file())
        self.assertIn("Games (games)", output)

    def test_malformed_existing_manifest_is_never_ignored(self):
        manifest = self.root / "app/Knowledge/Databases/Broken/Database.md"
        manifest.parent.mkdir(parents=True)
        manifest.write_text("not frontmatter\n", encoding="utf-8")
        with patch.object(initialization, "preflight", return_value=True), self.assertRaisesRegex(ValueError, "frontmatter"):
            initialization.initialize_new_instance(self.root, FakeUI("games"))

    def test_setup_only_runs_doctor_without_creating_state_or_marker(self):
        output = io.StringIO()
        with patch("doctor.diagnose", return_value=[]), contextlib.redirect_stdout(output):
            self.assertEqual(initialization.finish_setup(self.root, FakeUI()), 0)
        self.assertFalse((self.root / "app/Knowledge").exists())
        self.assertEqual(list(self.root.rglob("*init*")), [])
        self.assertIn("No knowledge was created", output.getvalue())

    def test_restore_preflight_allows_recoverable_knowledge_failure(self):
        failure = CheckResult("Knowledge", "knowledge.manifest-missing", "FAIL", "Synthetic failure")
        self.assertEqual(initialization.classify_health([failure], "restore").blockers, ())
        self.assertEqual(initialization.classify_health([failure], "restore", post_operation=True).blockers, (failure,))
        self.assertEqual(initialization.classify_health([failure], "new").blockers, (failure,))

    def test_restore_path_verifies_delegated_result(self):
        output = io.StringIO()

        def restored(root, **kwargs):
            shutil.copytree(GAMES_BLUEPRINT, root / "app/Knowledge/Databases/Games")
            return {"files_added": 1, "files_unchanged": 0, "git_files": 0}

        with patch.object(initialization, "preflight", return_value=True), \
                patch.object(initialization, "guided_restore", side_effect=restored), \
                patch("doctor.diagnose", return_value=[]), contextlib.redirect_stdout(output):
            self.assertEqual(initialization.initialize_from_backup(self.root, FakeUI()), 0)
        self.assertIn("Structural validation passed", output.getvalue())
        self.assertTrue((self.root / "app/Knowledge/Databases/Games").is_dir())

    def make_backup(self):
        source = self.root.parent / "Backup Source"
        note = source / "app/Knowledge/Inbox/Synthetic.md"
        note.parent.mkdir(parents=True)
        note.write_text("Synthetic private content\n", encoding="utf-8")
        specification = source / "app/Docs/Shard System Specification.md"
        specification.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "app/Docs/Shard System Specification.md", specification)
        archive = self.root.parent / "synthetic.sbbackup"
        backup(source, archive, PASSWORD)
        return archive

    def test_prompted_encrypted_restore_uses_shared_secure_flow(self):
        archive = self.make_backup()
        output = io.StringIO()
        with patch.object(initialization, "preflight", return_value=True), \
                patch("doctor.diagnose", return_value=[]), \
                patch("builtins.input", return_value=str(archive)), \
                patch("backup_restore.getpass.getpass", return_value=PASSWORD.decode()), \
                contextlib.redirect_stdout(output):
            self.assertEqual(initialization.initialize_from_backup(self.root, FakeUI()), 0)
        self.assertEqual(
            (self.root / "app/Knowledge/Inbox/Synthetic.md").read_text(encoding="utf-8"),
            "Synthetic private content\n",
        )
        self.assertIn("Restore complete", output.getvalue())
        self.assertIn("Database-semantic validity is not fully automated", output.getvalue())

    def test_wrong_restore_passphrase_writes_nothing(self):
        archive = self.make_backup()
        with patch.object(initialization, "preflight", return_value=True), \
                patch("builtins.input", return_value=str(archive)), \
                patch("backup_restore.getpass.getpass", return_value="wrong passphrase"), \
                self.assertRaisesRegex(BackupError, "authentication failed"):
            initialization.initialize_from_backup(self.root, FakeUI())
        self.assertFalse((self.root / "app/Knowledge").exists())

    def test_post_creation_verification_failure_preserves_database(self):
        issue = Issue(self.root / "app/Knowledge/Databases/Games", "synthetic", "failure")
        output = io.StringIO()
        with patch.object(initialization, "preflight", return_value=True), \
                patch.object(initialization, "structural_issues", return_value=([issue.path], [issue])), \
                patch("doctor.diagnose", return_value=[]), contextlib.redirect_stdout(output):
            status = initialization.initialize_new_instance(self.root, FakeUI("games"))
        self.assertEqual(status, 1)
        self.assertTrue((issue.path / "Database.md").is_file())
        self.assertIn("preserved for inspection", output.getvalue())

    def test_post_creation_verification_exception_preserves_database(self):
        output = io.StringIO()
        with patch.object(initialization, "preflight", return_value=True), \
                patch.object(initialization, "structural_issues", side_effect=OSError("synthetic failure")), \
                contextlib.redirect_stdout(output):
            status = initialization.initialize_new_instance(self.root, FakeUI("games"))
        self.assertEqual(status, 1)
        self.assertTrue((self.root / "app/Knowledge/Databases/Games/Database.md").is_file())
        self.assertIn("preserved for inspection", output.getvalue())

    def test_main_menu_eof_cancels_without_writes(self):
        with patch("builtins.input", side_effect=EOFError), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(shardbase.main(["init", "--root", str(self.root), "--no-color"]), 130)
        self.assertFalse((self.root / "app/Knowledge").exists())


if __name__ == "__main__":
    unittest.main()

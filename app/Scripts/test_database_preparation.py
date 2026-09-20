"""Local-only proof of preparation, manual movement, and preservation."""

import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from database_preparation import database_sources, new_id
from note_creation import CreationError, create_note
from shardbase import main
from validate_shardbase import NOTE_ID, parse_frontmatter, validate_database


SCRIPTS = Path(__file__).resolve().parent
BLUEPRINT = SCRIPTS.parent / "Blueprints/Games"


class DatabasePreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.blueprint = self.root / "app/Blueprints/Games"
        shutil.copytree(BLUEPRINT, self.blueprint)
        self.database = self.root / "app/Knowledge/Databases/My Games"
        shutil.copytree(self.blueprint, self.database)

    def create(self, title="Example", kind="core", **kwargs):
        return create_note(self.root, title, kind, intent="database", database="games", **kwargs)

    def edit_metadata(self, path, **fields):
        metadata, body = parse_frontmatter(path.read_text())
        metadata.update(fields)
        path.write_text("---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n" + body)

    def move(self, result):
        destination = result.suggested_path
        self.assertIsNotNone(destination)
        shutil.move(result.path, destination)
        self.assertEqual(validate_database(self.database), [])
        return destination

    def snapshot(self, directory):
        return {path.relative_to(directory): path.read_bytes() for path in directory.rglob("*") if path.is_file()}

    def test_core_is_ready_for_manual_move_with_id_preserved(self):
        before = self.snapshot(self.database)
        result = self.create("Example Game")
        metadata, body = parse_frontmatter(result.path.read_text())
        self.assertEqual(result.path.name, "Example Game.md")
        self.assertEqual(metadata["core"], "[[Example Game]]")
        self.assertRegex(metadata["id"], NOTE_ID)
        self.assertEqual(body, "# Example Game\n\n")
        self.assertEqual(before, self.snapshot(self.database))
        contents = result.path.read_bytes()
        destination = self.move(result)
        self.assertEqual(destination.read_bytes(), contents)

    def test_full_lineage_moves_without_metadata_or_filename_edits(self):
        core = self.move(self.create("Example: Game #1"))
        shard = self.create("Weapons", "shard", parent=core.stem)
        metadata, _ = parse_frontmatter(shard.path.read_text())
        self.assertEqual(shard.path.name, f"Weapons - {metadata['id']}.md")
        self.assertEqual(metadata["parent_note"], f"[[{core.stem}]]")
        shard_path = self.move(shard)
        pebble = self.create("Blade", "pebble", parent=f"[[{shard_path.stem}]]")
        metadata, _ = parse_frontmatter(pebble.path.read_text())
        self.assertEqual(metadata["core"], f"[[{core.stem}]]")
        self.assertEqual(metadata["parent_note"], f"[[{shard_path.stem}]]")
        self.move(pebble)

    def test_workspace_parent_preserves_placement_and_yaml_lineage(self):
        core = self.move(self.create())
        workspace = core.parent / core.stem
        workspace.mkdir()
        core = core.rename(workspace / core.name)
        result = self.create("Weapons", "shard", parent="Data/Game/Example/Example.md")
        self.assertEqual(result.suggested_path.parent, workspace)
        self.move(result)

    def test_supporting_notes_can_defer_lineage_but_have_canonical_ids_and_names(self):
        for kind in ("shard", "pebble"):
            result = self.create("Shared title", kind)
            metadata, _ = parse_frontmatter(result.path.read_text())
            self.assertRegex(metadata["id"], NOTE_ID)
            self.assertEqual(result.path.name, f"Shared title - {metadata['id']}.md")
            self.assertIsNone(metadata["core"])
            self.assertIsNone(metadata["parent_note"])
        self.assertEqual(len(list(result.path.parent.glob("*.md"))), 2)

    def test_existing_canonical_or_pending_id_collision_is_regenerated(self):
        core = self.move(self.create())
        self.edit_metadata(core, id="0000000000")
        draft = self.create("Pending")
        self.edit_metadata(draft.path, id="1111111111")
        # Move the pending note into a user-owned subfolder of Inbox.
        staged = draft.path.parent / "Staged"
        staged.mkdir()
        draft.path.rename(staged / draft.path.name)
        with patch("database_preparation.secrets.choice", side_effect=list("000000000011111111112222222222")):
            result = self.create("New")
        metadata, _ = parse_frontmatter(result.path.read_text())
        self.assertEqual(metadata["id"], "2222222222")

    def test_id_collision_retry_is_bounded(self):
        with patch("database_preparation.secrets.choice", return_value="0"):
            with self.assertRaisesRegex(CreationError, "unused note ID"):
                new_id({"0000000000"})

    def test_template_identity_and_lineage_are_not_copied(self):
        template = self.database / "Templates/Game.md"
        self.edit_metadata(template, id="0000000000", core="[[Other]]", parent_note="[[Other]]",
                           status="archived", tags=["games"], developers=["Example Studio"])
        before = self.snapshot(self.database)
        with patch("database_preparation.secrets.choice", side_effect=list("00000000001111111111")):
            result = self.create(alias="001")
        metadata, _ = parse_frontmatter(result.path.read_text())
        self.assertNotEqual(metadata["id"], "0000000000")
        self.assertEqual(metadata["core"], "[[Example]]")
        self.assertIsNone(metadata["parent_note"])
        self.assertEqual(metadata["status"], "draft")
        self.assertEqual(metadata["tags"], ["games"])
        self.assertEqual(metadata["developers"], ["Example Studio"])
        self.assertEqual(metadata["aliases"], ["001"])
        self.assertEqual(before, self.snapshot(self.database))

    def test_other_database_identity_and_template_are_selected(self):
        movies = self.root / "app/Knowledge/Databases/Personal Film Library"
        shutil.copytree(SCRIPTS / "fixtures/valid-database", movies)
        self.edit_metadata(movies / "Database.md", database_id="movies", database_name="Movies")
        templates = movies / "Templates"
        templates.mkdir()
        (templates / "Film.md").write_text("---\ntype: core\npool: Cinema\ntags: [film]\n---\n# Ignored\n")
        before = self.snapshot(movies)
        result = create_note(self.root, "Example Film", intent="database", database="movies")
        metadata, _ = parse_frontmatter(result.path.read_text())
        self.assertEqual(metadata["pool"], "Cinema")
        self.assertEqual(metadata["tags"], ["film"])
        self.assertEqual(result.template, templates / "Film.md")
        self.assertEqual(before, self.snapshot(movies))
        shutil.move(result.path, result.suggested_path)
        self.assertEqual(validate_database(movies), [])

    def test_blueprint_fallback_never_materializes_live_database(self):
        # Move only this test's disposable live copy out of discovery.
        self.database.rename(self.root / "unused-test-copy")
        result = self.create()
        self.assertEqual(result.template, self.blueprint / "Templates/Game.md")
        self.assertIsNone(result.suggested_path)
        self.assertFalse(self.database.exists())

    def test_live_contract_without_templates_uses_explicit_pool(self):
        shutil.rmtree(self.database / "Templates")
        with self.assertRaisesRegex(CreationError, "--pool"):
            self.create()
        result = self.create(pool="Games")
        self.assertIsNone(result.template)
        self.move(result)

    def test_multiple_templates_require_selection(self):
        template = self.database / "Templates/Game.md"
        shutil.copyfile(template, template.with_name("Other.md"))
        with self.assertRaisesRegex(CreationError, "Multiple templates"):
            self.create()
        result = self.create(template="Other.md")
        self.assertEqual(result.template.name, "Other.md")

    def test_multiple_collections_require_selection(self):
        self.edit_metadata(self.database / "Database.md", data_collections=["Game", "Other"])
        (self.database / "Data/Other/Attachments").mkdir(parents=True)
        with self.assertRaisesRegex(CreationError, "--collection"):
            self.create()
        result = self.create(collection="Other")
        self.assertEqual(result.suggested_path.parent, self.database / "Data/Other")
        self.move(result)

    def test_live_identity_wins_and_duplicate_live_owners_fail(self):
        sources = database_sources(self.root)
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].path, self.database)
        shutil.copytree(self.database, self.database.with_name("Duplicate"))
        with self.assertRaisesRegex(CreationError, "Multiple live"):
            self.create()

    def test_parent_errors_do_not_create_or_modify_files(self):
        core = self.move(self.create())
        pebble = self.move(self.create("Leaf", "pebble", parent=core.stem))
        before = self.snapshot(self.root)
        for options in (
            dict(kind="core", parent=core.stem),
            dict(kind="shard", parent=pebble.stem),
            dict(kind="shard", parent="Missing"),
            dict(kind="shard", parent="../../outside"),
            dict(kind="shard", parent=core.stem, pool="Other"),
            dict(kind="shard", parent=core.stem, collection="Other"),
        ):
            with self.subTest(options=options), self.assertRaises(CreationError):
                self.create("New", **options)
        self.assertEqual(before, self.snapshot(self.root))

    def test_target_collisions_are_checked_across_workspaces(self):
        core = self.move(self.create("Café"))
        workspace = core.parent / core.stem
        workspace.mkdir()
        core.rename(workspace / core.name)
        for title in ("Café", "Cafe\u0301", "CAFÉ"):
            with self.subTest(title=title), self.assertRaisesRegex(CreationError, "canonical filename"):
                self.create(title)

    def test_inbox_collision_preserves_existing_content(self):
        result = self.create()
        result.path.write_text("User content")
        with self.assertRaisesRegex(CreationError, "already uses"):
            self.create()
        self.assertEqual(result.path.read_text(), "User content")

    def test_plain_and_malformed_inbox_notes_do_not_block_preparation(self):
        inbox = self.root / "app/Knowledge/Inbox"
        inbox.mkdir()
        (inbox / "Plain.md").write_text("# Scratch\n")
        (inbox / "Malformed.md").write_text("---\nx: [unfinished\n")
        self.assertTrue(self.create().path.exists())

    def test_attachment_markdown_is_not_read_for_identity(self):
        attachment = self.database / "Data/Game/Attachments/Example.md"
        attachment.write_text("not frontmatter")
        self.assertTrue(self.create().path.exists())

    def test_symlink_boundaries_fail_without_reading_external_data(self):
        for relative in ("Templates/Game.md", "Data/Game/External"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as outside:
                path = self.database / relative
                original = path.read_bytes() if path.is_file() else None
                if original is not None:
                    path.unlink()
                path.symlink_to(outside, target_is_directory=True)
                with self.assertRaisesRegex(CreationError, "Symlink"):
                    self.create()
                self.assertEqual(list(Path(outside).iterdir()), [])
                path.unlink()
                if original is not None:
                    path.write_bytes(original)

    def test_invalid_database_options_and_metadata_fail_before_write(self):
        for options in (dict(database="missing"), dict(database="games", template="../Game.md"),
                        dict(database="games", collection="../Other"), dict(database="games", pool="")):
            with self.subTest(options=options), self.assertRaises(CreationError):
                create_note(self.root, "Example", intent="database", **options)
        self.edit_metadata(self.database / "Templates/Game.md", aliases=[False])
        with self.assertRaisesRegex(CreationError, "aliases"):
            self.create()
        self.assertFalse((self.root / "app/Knowledge/Inbox").exists())

    def test_unsupported_manifest_version_is_not_silently_interpreted(self):
        self.edit_metadata(self.database / "Database.md", manifest_version=2)
        with self.assertRaisesRegex(CreationError, "manifest_version"):
            self.create()

    def test_inbox_intent_rejects_database_options(self):
        with self.assertRaisesRegex(CreationError, "require --intent"):
            create_note(self.root, "Example", database="games")

    def test_trailing_heading_marker_is_reported_instead_of_wrong_filename(self):
        with self.assertRaisesRegex(CreationError, "heading markers"):
            self.create("Example ###")

    def test_interactive_database_selection_and_parent_selection(self):
        core = self.move(self.create())
        with patch("builtins.input", side_effect=["Weapons", "shard", "", "database", "games", "1"]), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["new", "--root", str(self.root)]), 0)
        path = next((self.root / "app/Knowledge/Inbox").glob("Weapons - *.md"))
        metadata, _ = parse_frontmatter(path.read_text())
        self.assertEqual(metadata["parent_note"], f"[[{core.stem}]]")
        self.assertIn("Manual move target:", output.getvalue())

    def test_cancel_database_selection_writes_nothing(self):
        before = self.snapshot(self.root)
        with patch("builtins.input", side_effect=["Example", "core", "", "database", KeyboardInterrupt()]), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["new", "--root", str(self.root)]), 130)
        self.assertEqual(before, self.snapshot(self.root))

    def test_interactive_selection_for_another_database_without_templates(self):
        movies = self.root / "app/Knowledge/Databases/Movies"
        shutil.copytree(SCRIPTS / "fixtures/valid-database", movies)
        self.edit_metadata(movies / "Database.md", database_id="movies", database_name="Movies",
                           data_collections=["Game", "Film"])
        (movies / "Data/Film/Attachments").mkdir(parents=True)
        with patch("builtins.input", side_effect=["Example Film", "core", "", "database", "movies", "Cinema", "Film"]), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["new", "--root", str(self.root)]), 0)
        path = self.root / "app/Knowledge/Inbox/Example Film.md"
        metadata, _ = parse_frontmatter(path.read_text())
        self.assertEqual(metadata["pool"], "Cinema")
        self.assertIn("Movies/Data/Film/Example Film.md", output.getvalue())

    def test_malformed_canonical_yaml_blocks_identity_scan_without_writes(self):
        (self.database / "Data/Game/Broken.md").write_text("---\nid: [unfinished\n")
        before = self.snapshot(self.root)
        with self.assertRaises(CreationError):
            self.create()
        self.assertEqual(before, self.snapshot(self.root))

    def test_invalid_parent_database_is_reported_before_writing(self):
        core = self.move(self.create())
        self.edit_metadata(core, parent_note="[[Missing]]")
        before = self.snapshot(self.root)
        with self.assertRaisesRegex(CreationError, "structural validation"):
            self.create("Child", "shard", parent=core.stem)
        self.assertEqual(before, self.snapshot(self.root))

    def test_inbox_symlink_during_identity_scan_is_refused(self):
        inbox = self.root / "app/Knowledge/Inbox"
        inbox.mkdir()
        with tempfile.TemporaryDirectory() as outside:
            (inbox / "External").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(CreationError, "Symlink"):
                self.create()
            self.assertEqual(list(Path(outside).iterdir()), [])

    def test_subprocess_proof_for_all_types_and_manual_moves(self):
        command = [sys.executable, "-B", str(SCRIPTS / "shardbase.py"), "new", "--root", str(self.root),
                   "--intent", "database", "--database", "games", "--alias", "", "--no-color"]
        parent = None
        for kind, title in (("core", "Example Game"), ("shard", "Example Topic"), ("pebble", "Example Detail")):
            args = command + ["--title", title, "--type", kind]
            if parent:
                args += ["--parent", parent]
            run = subprocess.run(args, input="", text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            paths = list((self.root / "app/Knowledge/Inbox").glob("*.md"))
            self.assertEqual(len(paths), 1)
            draft = paths[0]
            contents = draft.read_bytes()
            destination = self.database / "Data/Game" / draft.name
            shutil.move(draft, destination)
            self.assertEqual(destination.read_bytes(), contents)
            self.assertEqual(validate_database(self.database), [])
            parent = destination.stem
        self.assertEqual(list(self.root.rglob("__pycache__")), [])


if __name__ == "__main__":
    unittest.main()

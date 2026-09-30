"""Local-only proof of retained canonical preparation and safe commit primitives."""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from _support import FIXTURES, GAMES_BLUEPRINT
from database_preparation import database_sources, prepare_note
from note_creation import CreationError, commit_canonical, create_note, new_id
from validate_shardbase import NOTE_ID, parse_frontmatter, validate_database


class DatabasePreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.blueprint = self.root / "app/Blueprints/Games"
        shutil.copytree(GAMES_BLUEPRINT, self.blueprint)
        self.database = self.root / "app/Knowledge/Databases/My Games"
        shutil.copytree(self.blueprint, self.database)

    def create(self, title="Example", kind="core", **kwargs):
        prepared = prepare_note(
            self.root, title, kind, kwargs.pop("alias", None), kwargs.pop("database", "games"),
            kwargs.pop("template", None), kwargs.pop("pool", None), kwargs.pop("parent", None),
            kwargs.pop("collection", None), kwargs.pop("core", None),
        )
        self.assertEqual(kwargs, {})
        return commit_canonical(self.root, prepared)

    def edit_metadata(self, path, **fields):
        metadata, body = parse_frontmatter(path.read_text())
        metadata.update(fields)
        path.write_text("---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n" + body)

    def created_path(self, result):
        self.assertTrue(result.path.is_relative_to(self.database))
        self.assertEqual(validate_database(self.database), [])
        self.assertFalse((self.root / "app/Knowledge/Inbox").exists())
        return result.path

    def snapshot(self, directory):
        return {path.relative_to(directory): path.read_bytes() for path in directory.rglob("*") if path.is_file()}

    def test_core_is_created_directly_with_stable_id(self):
        before = self.snapshot(self.database)
        result = self.create("Example Game")
        metadata, body = parse_frontmatter(result.path.read_text())
        self.assertEqual(result.path.name, "Example Game.md")
        self.assertEqual(metadata["core"], "[[Example Game]]")
        self.assertRegex(metadata["id"], NOTE_ID)
        self.assertEqual(body, "# Example Game\n\n")
        self.assertEqual(before, {p: data for p, data in self.snapshot(self.database).items() if p != result.path.relative_to(self.database)})
        contents = result.path.read_bytes()
        destination = self.created_path(result)
        self.assertEqual(destination.read_bytes(), contents)

    def test_full_lineage_is_created_without_metadata_or_filename_edits(self):
        core = self.created_path(self.create("Example: Game #1"))
        shard = self.create("Weapons", "shard", parent=core.stem)
        metadata, _ = parse_frontmatter(shard.path.read_text())
        self.assertEqual(shard.path.name, f"Weapons - {metadata['id']}.md")
        self.assertEqual(metadata["parent_note"], f"[[{core.stem}]]")
        shard_path = self.created_path(shard)
        pebble = self.create("Blade", "pebble", parent=f"[[{shard_path.stem}]]")
        metadata, _ = parse_frontmatter(pebble.path.read_text())
        self.assertEqual(metadata["core"], f"[[{core.stem}]]")
        self.assertEqual(metadata["parent_note"], f"[[{shard_path.stem}]]")
        self.created_path(pebble)

    def test_workspace_parent_preserves_placement_and_yaml_lineage(self):
        core = self.created_path(self.create())
        workspace = core.parent
        result = self.create("Weapons", "shard", parent="Data/Game/Example/Example.md")
        self.assertEqual(result.path.parent, workspace)
        self.created_path(result)

    def test_supporting_notes_require_complete_lineage(self):
        before = self.snapshot(self.root)
        for kind in ("shard", "pebble"):
            for parent in (None, ""):
                with self.subTest(kind=kind, parent=parent), self.assertRaisesRegex(CreationError, "require --parent"):
                    self.create("Shared title", kind, parent=parent)
        self.assertEqual(before, self.snapshot(self.root))

    def test_existing_canonical_or_pending_id_collision_is_regenerated(self):
        core = self.created_path(self.create())
        self.edit_metadata(core, id="0000000000")
        draft = create_note(self.root, "Pending")
        self.edit_metadata(draft.path, id="1111111111")
        staged = draft.path.parent / "Staged"
        staged.mkdir()
        draft.path.rename(staged / draft.path.name)
        with patch("note_creation.secrets.choice", side_effect=list("000000000011111111112222222222")):
            result = self.create("New")
        metadata, _ = parse_frontmatter(result.path.read_text())
        self.assertEqual(metadata["id"], "2222222222")

    def test_id_collision_retry_is_bounded(self):
        with patch("note_creation.secrets.choice", return_value="0"):
            with self.assertRaisesRegex(CreationError, "unused note ID"):
                new_id({"0000000000"})

    def test_template_identity_and_lineage_are_not_copied(self):
        template = self.database / "Templates/Game.md"
        self.edit_metadata(template, id="0000000000", core="[[Other]]", parent_note="[[Other]]",
                           status="archived", tags=["games"], developers=["Example Studio"])
        before = self.snapshot(self.database)
        with patch("note_creation.secrets.choice", side_effect=list("00000000001111111111")):
            result = self.create(alias="001")
        metadata, _ = parse_frontmatter(result.path.read_text())
        self.assertNotEqual(metadata["id"], "0000000000")
        self.assertEqual(metadata["core"], "[[Example]]")
        self.assertIsNone(metadata["parent_note"])
        self.assertEqual(metadata["status"], "draft")
        self.assertEqual(metadata["tags"], ["games"])
        self.assertEqual(metadata["developers"], ["Example Studio"])
        self.assertEqual(metadata["aliases"], ["001"])
        self.assertEqual(before, {p: data for p, data in self.snapshot(self.database).items() if p != result.path.relative_to(self.database)})

    def test_other_database_identity_and_template_are_selected(self):
        movies = self.root / "app/Knowledge/Databases/Personal Film Library"
        shutil.copytree(FIXTURES / "valid-database", movies)
        self.edit_metadata(movies / "Database.md", database_id="movies", database_name="Movies")
        templates = movies / "Templates"
        templates.mkdir()
        (templates / "Film.md").write_text("---\ntype: core\npool: Cinema\ntags: [film]\n---\n# Ignored\n")
        before = self.snapshot(movies)
        result = self.create("Example Film", database="movies")
        metadata, _ = parse_frontmatter(result.path.read_text())
        self.assertEqual(metadata["pool"], "Cinema")
        self.assertEqual(metadata["tags"], ["film"])
        self.assertEqual(result.template, templates / "Film.md")
        self.assertEqual(before, {p: data for p, data in self.snapshot(movies).items() if p != result.path.relative_to(movies)})
        self.assertEqual(validate_database(movies), [])

    def test_blueprint_fallback_never_materializes_live_database(self):
        # Move only this test's disposable live copy out of discovery.
        self.database.rename(self.root / "unused-test-copy")
        before = self.snapshot(self.root)
        with self.assertRaisesRegex(CreationError, "create/materialize"):
            self.create()
        self.assertEqual(before, self.snapshot(self.root))
        self.assertFalse(self.database.exists())

    def test_live_contract_without_templates_uses_explicit_pool(self):
        shutil.rmtree(self.database / "Templates")
        with self.assertRaisesRegex(CreationError, "--pool"):
            self.create()
        result = self.create(pool="Games")
        self.assertIsNone(result.template)
        self.created_path(result)

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
        self.assertEqual(result.path.parent, self.database / "Data/Other/Example")
        self.created_path(result)

    def test_live_identity_wins_and_duplicate_live_owners_fail(self):
        sources = database_sources(self.root)
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].path, self.database)
        shutil.copytree(self.database, self.database.with_name("Duplicate"))
        with self.assertRaisesRegex(CreationError, "Multiple live"):
            self.create()

    def test_parent_errors_do_not_create_or_modify_files(self):
        core = self.created_path(self.create())
        pebble = self.created_path(self.create("Leaf", "pebble", parent=core.stem))
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
        self.created_path(self.create("Café"))
        for title in ("Café", "Cafe\u0301", "CAFÉ"):
            with self.subTest(title=title), self.assertRaisesRegex(CreationError, "canonical filename"):
                self.create(title)

    def test_invalid_existing_database_preserves_content(self):
        result = self.create()
        result.path.write_text("User content")
        with self.assertRaisesRegex(CreationError, "frontmatter"):
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
                self.create("Example", **options)
        self.edit_metadata(self.database / "Templates/Game.md", aliases=[False])
        with self.assertRaisesRegex(CreationError, "aliases"):
            self.create()
        self.assertFalse((self.root / "app/Knowledge/Inbox").exists())

    def test_unsupported_manifest_version_is_not_silently_interpreted(self):
        self.edit_metadata(self.database / "Database.md", manifest_version=2)
        with self.assertRaisesRegex(CreationError, "manifest_version"):
            self.create()

    def test_trailing_heading_marker_is_reported_instead_of_wrong_filename(self):
        with self.assertRaisesRegex(CreationError, "heading markers"):
            self.create("Example ###")

    def test_malformed_canonical_yaml_blocks_identity_scan_without_writes(self):
        (self.database / "Data/Game/Broken.md").write_text("---\nid: [unfinished\n")
        before = self.snapshot(self.root)
        with self.assertRaises(CreationError):
            self.create()
        self.assertEqual(before, self.snapshot(self.root))

    def test_invalid_parent_database_is_reported_before_writing(self):
        core = self.created_path(self.create())
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

    def test_core_placement_preferences_and_portable_stem(self):
        manifest = self.database / "Database.md"
        for index, preference in enumerate((None, {}, {"core_placement": "workspace"}, {"core_placement": "flat"})):
            metadata, body = parse_frontmatter(manifest.read_text())
            metadata.pop("creation_defaults", None)
            if preference is not None:
                metadata["creation_defaults"] = preference
            manifest.write_text("---\n" + yaml.safe_dump(metadata) + "---\n" + body)
            result = self.create(f"Example: Game #{index}")
            expected_parent = self.database / "Data/Game"
            if preference != {"core_placement": "flat"}:
                expected_parent /= f"Example Game {index}"
            self.assertEqual(result.path.parent, expected_parent)
            self.assertEqual(result.path.name, f"Example Game {index}.md")
            metadata, _ = parse_frontmatter(result.path.read_text())
            self.assertRegex(metadata["id"], NOTE_ID)
            self.assertEqual(metadata["status"], "draft")
            self.assertEqual(metadata["core"], f"[[Example Game {index}]]")
            self.assertEqual(validate_database(self.database), [])

    def test_invalid_creation_defaults_block_validator_and_creator(self):
        for value in (None, "workspace", [], False, {1: "workspace"}, {"core_placement": None},
                      {"core_placement": []}, {"core_placement": {}}, {"core_placement": "other"}):
            with self.subTest(value=value):
                self.edit_metadata(self.database / "Database.md", creation_defaults=value)
                self.assertIn("manifest-creation-defaults", {issue.code for issue in validate_database(self.database)})
                before = self.snapshot(self.root)
                with self.assertRaisesRegex(CreationError, "creation_defaults"):
                    self.create()
                self.assertEqual(before, self.snapshot(self.root))

    def test_extra_manifest_fields_remain_supported(self):
        self.edit_metadata(self.database / "Database.md", custom={"database": "setting"},
                           creation_defaults={"custom": True, "core_placement": "workspace"})
        self.created_path(self.create())

    def test_existing_flat_lineage_stays_flat_after_preference_changes(self):
        manifest = self.database / "Database.md"
        self.edit_metadata(manifest, creation_defaults={"core_placement": "flat"})
        core = self.created_path(self.create())
        self.edit_metadata(manifest, creation_defaults={"core_placement": "workspace"})
        for kind in ("shard", "pebble"):
            note = self.created_path(self.create(kind, kind, core=core.stem, parent=core.stem))
            self.assertEqual(note.parent, core.parent)
            self.assertFalse((core.parent / core.stem).exists())
        self.assertEqual(validate_database(self.database), [])

    def test_core_and_parent_must_agree_and_be_correct_types(self):
        first = self.created_path(self.create("First"))
        second = self.created_path(self.create("Second"))
        shard = self.created_path(self.create("Topic", "shard", parent=first.stem))
        before = self.snapshot(self.root)
        for core, parent in ((first.stem, second.stem), (second.stem, shard.stem), (shard.stem, first.stem),
                             ("Missing", first.stem), (first.stem, ""), ("", first.stem)):
            with self.subTest(core=core, parent=parent), self.assertRaises(CreationError):
                self.create("Child", "pebble", core=core, parent=parent)
        self.assertEqual(before, self.snapshot(self.root))

    def test_supporting_inheritance_overrides_template_defaults(self):
        self.edit_metadata(self.database / "Database.md", data_collections=["Game", "Other"])
        (self.database / "Data/Other/Attachments").mkdir(parents=True)
        core = self.created_path(self.create("Root", collection="Other", pool="Selected Pool"))
        for kind in ("shard", "pebble"):
            note = self.created_path(self.create(kind, kind, core=core.stem, parent=core.stem))
            metadata, _ = parse_frontmatter(note.read_text())
            self.assertEqual(note.parent, core.parent)
            self.assertEqual(metadata["pool"], "Selected Pool")
            self.assertEqual(metadata["core"], "[[Root]]")
            self.assertEqual(metadata["parent_note"], "[[Root]]")
            self.assertEqual(note.name, f"{kind} - {metadata['id']}.md")

    def test_eligible_parents_filter_other_lineages_and_pebbles(self):
        from database_preparation import (
            eligible_parents,
            select_database,
            validated_notes,
        )
        first = self.created_path(self.create("First"))
        second = self.created_path(self.create("Second"))
        topic = self.created_path(self.create("Topic", "shard", parent=first.stem))
        self.created_path(self.create("Leaf", "pebble", parent=first.stem))
        self.created_path(self.create("Unrelated", "shard", parent=second.stem))
        source = select_database(self.root, "games")
        notes = validated_notes(self.root, source)
        root = next(note for note in notes if note.path == first)
        self.assertEqual({note.path for note in eligible_parents(source, notes, root)}, {first, topic})

    def test_split_lineages_fail_preflight(self):
        core = self.created_path(self.create())
        shard = self.created_path(self.create("Topic", "shard", parent=core.stem))
        shard.rename(core.parent.parent / shard.name)
        before = self.snapshot(self.root)
        self.assertIn("workspace-split", {issue.code for issue in validate_database(self.database)})
        with self.assertRaisesRegex(CreationError, "structural validation"):
            self.create("Child", "shard", parent=core.stem)
        self.assertEqual(before, self.snapshot(self.root))

    def test_flat_lineage_cannot_cross_collections(self):
        self.edit_metadata(self.database / "Database.md", data_collections=["Game", "Other"],
                           creation_defaults={"core_placement": "flat"})
        (self.database / "Data/Other/Attachments").mkdir(parents=True)
        core = self.created_path(self.create(collection="Game"))
        shard = self.created_path(self.create("Topic", "shard", parent=core.stem))
        shard.rename(self.database / "Data/Other" / shard.name)
        self.assertIn("lineage-collection", {issue.code for issue in validate_database(self.database)})
        with self.assertRaisesRegex(CreationError, "structural validation"):
            self.create("New", collection="Game")

    def test_workspace_collisions_preserve_existing_entries(self):
        for name in ("Example", "example", "Attachments"):
            with self.subTest(name=name):
                entry = self.database / "Data/Game" / name
                if name != "Attachments":
                    entry.write_text("Existing resource")
                before = self.snapshot(self.root)
                with self.assertRaisesRegex(CreationError, "already uses"):
                    self.create("Attachments" if name == "Attachments" else "Example")
                self.assertEqual(before, self.snapshot(self.root))
                if name != "Attachments":
                    entry.unlink()

    def test_post_validation_failure_rolls_back_new_workspace_and_file(self):
        from validate_shardbase import Issue
        before = self.snapshot(self.root)
        with patch("validate_shardbase.validate_database", return_value=[Issue(self.database, "test", "forced failure")]):
            with self.assertRaisesRegex(CreationError, "Post-write"):
                self.create()
        self.assertEqual(before, self.snapshot(self.root))
        self.assertFalse((self.database / "Data/Game/Example").exists())

    def test_rollback_keeps_existing_workspace_and_unrelated_contents(self):
        core = self.created_path(self.create())
        before = self.snapshot(self.root)
        with patch("validate_shardbase.validate_database", side_effect=OSError("verification failure")):
            with self.assertRaisesRegex(OSError, "verification failure"):
                self.create("Topic", "shard", parent=core.stem)
        self.assertTrue(core.parent.is_dir())
        self.assertEqual(before, self.snapshot(self.root))

    def test_rollback_preserves_new_unrelated_workspace_file(self):
        workspace = self.database / "Data/Game/Example"
        def fail(_):
            (workspace / "Other.txt").write_text("Concurrent content")
            raise OSError("verification failure")
        with patch("validate_shardbase.validate_database", side_effect=fail), self.assertRaises(OSError):
            self.create()
        self.assertEqual(list(workspace.iterdir()), [workspace / "Other.txt"])
        self.assertEqual((workspace / "Other.txt").read_text(), "Concurrent content")

    def test_competing_file_is_never_removed_or_truncated(self):
        original_open = Path.open
        def competing_open(path, mode="r", *args, **kwargs):
            if mode == "x":
                path.write_text("Competing content")
            return original_open(path, mode, *args, **kwargs)
        with patch.object(Path, "open", competing_open), self.assertRaises(FileExistsError):
            self.create()
        self.assertEqual((self.database / "Data/Game/Example/Example.md").read_text(), "Competing content")

    def test_competing_workspace_is_preserved(self):
        original_mkdir = Path.mkdir
        workspace = self.database / "Data/Game/Example"
        def competing_mkdir(path, *args, **kwargs):
            if path == workspace:
                original_mkdir(path)
                (path / "Other.txt").write_text("Competing content")
            return original_mkdir(path, *args, **kwargs)
        with patch.object(Path, "mkdir", competing_mkdir), self.assertRaises(FileExistsError):
            self.create()
        self.assertEqual(list(workspace.iterdir()), [workspace / "Other.txt"])

    def test_interrupted_partial_write_rolls_back(self):
        original_open = Path.open
        class InterruptedWriter:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.stream.close()
            def fileno(self):
                return self.stream.fileno()
            def write(self, document):
                self.stream.write(document[:10])
                raise KeyboardInterrupt()
        def interrupted_open(path, mode="r", *args, **kwargs):
            stream = original_open(path, mode, *args, **kwargs)
            return InterruptedWriter(stream) if mode == "x" else stream
        before = self.snapshot(self.root)
        with patch.object(Path, "open", interrupted_open), self.assertRaises(KeyboardInterrupt):
            self.create()
        self.assertEqual(before, self.snapshot(self.root))
        self.assertFalse((self.database / "Data/Game/Example").exists())

    def test_missing_or_malformed_live_identity_blocks_creation(self):
        other = self.database.with_name("Unfinished")
        other.mkdir()
        before = self.snapshot(self.root)
        with self.assertRaisesRegex(CreationError, "Missing live database manifest"):
            self.create()
        self.assertEqual(before, self.snapshot(self.root))
        (other / "Database.md").write_text("---\ndatabase_id: []\n---\n")
        before = self.snapshot(self.root)
        with self.assertRaisesRegex(CreationError, "database_id"):
            self.create()
        self.assertEqual(before, self.snapshot(self.root))

    def test_rollback_preserves_replacement_of_new_file(self):
        path = self.database / "Data/Game/Example/Example.md"
        def replace_and_fail(_):
            # Keep the original inode allocated so the replacement is distinct.
            path.rename(self.root / "original-test-note.md")
            path.write_text("Replacement content")
            raise OSError("verification failure")
        with patch("validate_shardbase.validate_database", side_effect=replace_and_fail), self.assertRaises(OSError):
            self.create()
        self.assertEqual(path.read_text(), "Replacement content")

    def test_normalized_workspace_resource_collision_writes_nothing(self):
        entry = self.database / "Data/Game/Café"
        entry.write_text("Existing resource")
        before = self.snapshot(self.root)
        for title in ("Cafe\u0301", "CAFÉ"):
            with self.subTest(title=title), self.assertRaisesRegex(CreationError, "already uses"):
                self.create(title)
        self.assertEqual(before, self.snapshot(self.root))


if __name__ == "__main__":
    unittest.main()

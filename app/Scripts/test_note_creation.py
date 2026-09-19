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

from note_creation import CreationError, create_note
from shardbase import Terminal, main
from validate_shardbase import parse_frontmatter, validate_database

SCRIPTS = Path(__file__).resolve().parent
BLUEPRINT = SCRIPTS.parent / "Blueprints/Games"

class NoteCreationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.blueprint = self.root / "app/Blueprints/Games"
        shutil.copytree(BLUEPRINT, self.blueprint)

    def template_field(self, field, value, source=None, remove=False):
        path = (source or self.blueprint) / "Templates/Game.md"
        metadata, body = parse_frontmatter(path.read_text())
        if remove:
            metadata.pop(field)
        else:
            metadata[field] = value
        path.write_text("---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n" + body)

    def live_database(self, name="My Games"):
        database = self.root / "app/Knowledge/Databases" / name
        shutil.copytree(self.blueprint, database)
        return database

    def assert_no_capture(self):
        self.assertFalse((self.root / "app/Knowledge/Inbox").exists())

    def test_inbox_draft_has_required_yaml_and_only_h1(self):
        result = create_note(self.root, "Example Game")
        self.assertEqual(result.path, self.root / "app/Knowledge/Inbox/Example Game.md")
        metadata, body = parse_frontmatter(result.path.read_text())
        self.assertEqual(metadata, dict(type="core", pool="Games", core="[[Example Game]]", parent_note=None, status="draft", aliases=None, id=None, tags=None))
        self.assertEqual(body, "# Example Game\n\n")
        self.assertIn("aliases:\nid:\ntags:\n", result.path.read_text())
        self.assertFalse((self.root / "app/Knowledge/Inbox/Staged").exists())
        self.assertFalse((self.root / "app/Knowledge/Databases").exists())

    def test_existing_staged_capture_is_preserved(self):
        staged = self.root / "app/Knowledge/Inbox/Staged"
        staged.mkdir(parents=True)
        capture = staged / "Example.md"
        capture.write_text("User-authored staged content\n")
        result = create_note(self.root, "Example")
        self.assertEqual(result.path, staged.parent / "Example.md")
        self.assertEqual(capture.read_text(), "User-authored staged content\n")
        self.assertEqual(list(staged.iterdir()), [capture])

    def test_rendered_note_conforms_after_deliberate_test_promotion(self):
        database = self.live_database()
        result = create_note(self.root, "Example: Game #1")
        self.assertEqual(result.template, database / "Templates/Game.md")
        self.assertEqual(list((database / "Data/Game").glob("*.md")), [])
        promoted = database / "Data/Game" / result.path.name
        shutil.copyfile(result.path, promoted)
        metadata, body = parse_frontmatter(promoted.read_text())
        metadata["id"] = "0a1b2c3d4e"
        promoted.write_text("---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False) + "---\n" + body, encoding="utf-8")
        self.assertEqual(validate_database(database), [])

    def test_live_template_defaults_preserved_and_body_ignored(self):
        database = self.live_database()
        for field, value in (("tags", ["games"]), ("aliases", ["Alternate"]), ("id", "001"), ("developers", ["Example Studio"]), ("play_state", "not_started"), ("release_date", "2026-01-02")):
            self.template_field(field, value, database)
        path = database / "Templates/Game.md"
        path.write_text(path.read_text() + "## User template section\n\nSome prose.\n")
        before = {p: p.read_bytes() for p in database.rglob("*") if p.is_file()}
        result = create_note(self.root, "Example")
        metadata, body = parse_frontmatter(result.path.read_text())
        self.assertEqual(metadata["id"], "001")
        self.assertEqual(metadata["tags"], ["games"])
        self.assertEqual(metadata["developers"], ["Example Studio"])
        self.assertEqual(body, "# Example\n\n")
        self.assertEqual(before, {p: p.read_bytes() for p in database.rglob("*") if p.is_file()})

    def test_missing_live_template_does_not_fall_back_or_sync(self):
        database = self.live_database()
        (database / "Templates/Game.md").unlink()
        with self.assertRaisesRegex(CreationError, "Missing"):
            create_note(self.root, "Example")
        self.assertFalse((database / "Templates/Game.md").exists())
        self.assert_no_capture()

    def test_incomplete_databases_do_not_block_capture(self):
        database = self.live_database()
        other = self.root / "app/Knowledge/Databases/Unfinished"
        other.mkdir()
        result = create_note(self.root, "Example", "shard")
        self.assertEqual(result.template, database / "Templates/Game Shard.md")
        self.assertTrue(result.path.exists())

    def test_manifest_conformance_is_not_a_creation_gate(self):
        database = self.live_database()
        path = database / "Database.md"
        path.write_text("---\ndatabase_id: games\nmanifest_version: future\ndata_collections: [Missing]\ndatabase_status: archived\n---\nIncomplete contract\n")
        result = create_note(self.root, "Example", "pebble")
        self.assertEqual(result.template, database / "Templates/Game Pebble.md")
        self.assertTrue(result.path.exists())

    def test_unverified_template_metadata_is_preserved_for_review(self):
        fields = dict(pool="Unreviewed", core="[[Missing Core]]", parent_note="[[Missing Parent]]",
                      status="unreviewed", tags=[False], id=123, play_state="unknown",
                      developers=None, release_date="2026-02-30", custom_field={"value": True})
        for field, value in fields.items():
            self.template_field(field, value)
        result = create_note(self.root, "Example")
        metadata, body = parse_frontmatter(result.path.read_text())
        for field, value in fields.items():
            self.assertEqual(metadata[field], value)
        self.assertEqual(body, "# Example\n\n")

    def test_missing_template_fields_receive_editable_defaults(self):
        path = self.blueprint / "Templates/Game Shard.md"
        path.write_text("---\ncustom_field: unreviewed\n---\n")
        result = create_note(self.root, "Example", "shard")
        metadata, body = parse_frontmatter(result.path.read_text())
        self.assertEqual(metadata, dict(type="shard", pool="Games", core=None, parent_note=None,
                                       status="draft", aliases=None, id=None, tags=None,
                                       custom_field="unreviewed"))
        self.assertEqual(body, "# Example\n\n")

    def test_yaml_errors_do_not_write_or_echo_template_content(self):
        path = self.blueprint / "Templates/Game.md"
        for text in ("---\nsecret: [sensitive-example-value\n---\n", "---\nsecret: sensitive-example-value\nsecret: sensitive-example-value\n---\n"):
            path.write_text(text)
            with self.assertRaises(CreationError) as caught:
                create_note(self.root, "Example")
            self.assertNotIn("sensitive-example-value", str(caught.exception))
            self.assert_no_capture()

    def test_portable_names_preserve_display_title_and_yaml_safety(self):
        for title, filename in (("Example: Game #1", "Example Game 1.md"), ('Game [Remastered] "Edition"', "Game Remastered Edition.md"), ("CON", "_CON.md"), ("Game. .", "Game.md"), ("Café 🎮", "Café 🎮.md"), ("on", "on.md"), ("../Outside", ".. Outside.md")):
            with self.subTest(title=title):
                result = create_note(self.root, title)
                self.assertEqual(result.path.name, filename)
                metadata, body = parse_frontmatter(result.path.read_text())
                self.assertEqual(body, f"# {title}\n\n")
                self.assertEqual(metadata["core"], f"[[{filename[:-3]}]]")

    def test_empty_and_multiline_titles_refused(self):
        for title in ("", "   ", "...", "[]/#", "Title\nInjected", "Title\x00Injected", "Title\u2028Injected"):
            with self.subTest(title=title):
                with self.assertRaises(CreationError):
                    create_note(self.root, title)
                self.assert_no_capture()

    def test_existing_file_and_normalized_collisions_never_overwritten(self):
        first = create_note(self.root, "Game: One")
        first.path.write_text("User-edited content")
        for title in ("Game: One", "Game One", "game one"):
            with self.assertRaisesRegex(CreationError, "already uses"):
                create_note(self.root, title)
            self.assertEqual(first.path.read_text(), "User-edited content")
        self.assertEqual(list(first.path.parent.iterdir()), [first.path])

    def test_unicode_equivalent_collisions_refused(self):
        create_note(self.root, "Café")
        with self.assertRaises(CreationError):
            create_note(self.root, "Cafe\u0301")

    def test_symlink_boundaries_refused(self):
        for relative in ("app/Knowledge", "app/Knowledge/Inbox", "app/Knowledge/Databases"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as outside:
                path = self.root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(outside, target_is_directory=True)
                with self.assertRaises(CreationError):
                    create_note(self.root, "Example")
                self.assertEqual(list(Path(outside).iterdir()), [])
                path.unlink()

    def test_symlink_template_refused_before_reading(self):
        path = self.blueprint / "Templates/Game.md"
        path.unlink()
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "private.md"
            target.write_text("private content")
            path.symlink_to(target)
            with self.assertRaisesRegex(CreationError, "Symlink"):
                create_note(self.root, "Example")
        self.assert_no_capture()

    def test_dangling_destination_symlink_never_followed(self):
        directory = self.root / "app/Knowledge/Inbox"
        directory.mkdir(parents=True)
        target = self.root / "absent.md"
        (directory / "Example.md").symlink_to(target)
        with self.assertRaises(CreationError):
            create_note(self.root, "Example")
        self.assertFalse(target.exists())

    def test_exclusive_open_preserves_competing_file(self):
        original_open = Path.open
        def competing_open(path, mode="r", *args, **kwargs):
            if mode == "x":
                path.write_text("Competing content")
            return original_open(path, mode, *args, **kwargs)
        with patch.object(Path, "open", competing_open):
            with self.assertRaises(FileExistsError):
                create_note(self.root, "Example")
        self.assertEqual((self.root / "app/Knowledge/Inbox/Example.md").read_text(), "Competing content")

    def test_prompts_reprompt_and_create(self):
        with patch("builtins.input", side_effect=["Example", "invalid", "1", ""]) as prompts, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["new", "--root", str(self.root)]), 0)
        self.assertEqual(prompts.call_count, 4)
        self.assertIn("Choose 1", output.getvalue())
        self.assertIn("Saved to Inbox", output.getvalue())
        self.assertNotIn("Destination", output.getvalue())
        self.assertTrue((self.root / "app/Knowledge/Inbox/Example.md").is_file())
        self.assertFalse((self.root / "app/Knowledge/Inbox/Staged").exists())

    def test_cancelled_prompts_write_nothing(self):
        for error in (EOFError(), KeyboardInterrupt()):
            with patch("builtins.input", side_effect=["Example", error]), contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["new", "--root", str(self.root)]), 130)
            self.assert_no_capture()

    def test_subprocess_flags_help_and_errors(self):
        command = [sys.executable, "-B", str(SCRIPTS / "shardbase.py")]
        help_result = subprocess.run(command + ["--help"], capture_output=True, text=True, cwd=self.root)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("new", help_result.stdout)
        new_help = subprocess.run(command + ["new", "--help"], capture_output=True, text=True)
        self.assertEqual(new_help.returncode, 0)
        self.assertIn("app/Knowledge/Inbox/", new_help.stdout)
        self.assertNotIn("--destination", new_help.stdout)
        args = ["new", "--root", str(self.root), "--title", "Example", "--type", "core", "--alias", ""]
        created = subprocess.run(command + args, input="", capture_output=True, text=True, cwd=self.root)
        self.assertEqual(created.returncode, 0, created.stderr)
        self.assertTrue((self.root / "app/Knowledge/Inbox/Example.md").is_file())
        self.assertFalse((self.root / "app/Knowledge/Inbox/Staged").exists())
        collision = subprocess.run(command + args, capture_output=True, text=True)
        self.assertEqual(collision.returncode, 1)
        self.assertNotIn("Traceback", collision.stderr)
        for destination in ("inbox", "databases"):
            with self.subTest(destination=destination):
                invalid = subprocess.run(command + args + ["--destination", destination], input="", capture_output=True, text=True)
                self.assertEqual(invalid.returncode, 2)
                self.assertIn("unrecognized arguments: --destination", invalid.stderr)
        self.assertEqual(list(self.root.rglob("__pycache__")), [])










    def test_terminal_color_is_optional_and_control_characters_are_inert(self):
        with patch("sys.stdout.isatty", return_value=True), patch.dict("os.environ", {"TERM": "xterm"}, clear=True):
            self.assertIn("\033[", Terminal().style("Title"))
            self.assertNotIn("\033[", Terminal(no_color=True).style("Title"))
            with patch.dict("os.environ", {"NO_COLOR": ""}):
                self.assertNotIn("\033[", Terminal().style("Title"))
        with patch("sys.stdout.isatty", return_value=False):
            self.assertEqual(Terminal().style("Title\033[2J"), "Title [2J")

    def test_all_types_create_in_inbox_without_ancestors(self):
        for kind in ("core", "shard", "pebble"):
            with self.subTest(kind=kind):
                result = create_note(self.root, f"Example {kind}", kind)
                metadata, body = parse_frontmatter(result.path.read_text())
                self.assertEqual(metadata, dict(type=kind, pool="Games",
                    core=f"[[Example {kind}]]" if kind == "core" else None,
                    parent_note=None, status="draft", aliases=None, id=None, tags=None))
                self.assertEqual(body, f"# Example {kind}\n\n")
                self.assertEqual(result.path, self.root / "app/Knowledge/Inbox" / f"Example {kind}.md")
        self.assertFalse((self.root / "app/Knowledge/Inbox/Staged").exists())
        self.assertFalse((self.root / "app/Knowledge/Databases").exists())

    def test_alias_prompt_finishes_capture_without_parent_or_destination_prompt(self):
        with patch("builtins.input", side_effect=["Terminus", "2", "Island"]) as prompts, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["new", "--root", str(self.root)]), 0)
        self.assertEqual(prompts.call_count, 3)
        self.assertIn("Alias", prompts.call_args_list[2].args[0])
        self.assertNotIn("Parent note", output.getvalue())
        self.assertNotIn("Destination", output.getvalue())
        path = self.root / "app/Knowledge/Inbox/Terminus.md"
        metadata, _ = parse_frontmatter(path.read_text())
        self.assertEqual(metadata["type"], "shard")
        self.assertEqual(metadata["aliases"], ["Island"])
        self.assertIsNone(metadata["core"])
        self.assertIsNone(metadata["parent_note"])

    def test_optional_alias_is_a_yaml_string_list_or_blank(self):
        for index, alias in enumerate((None, "", "   ", "Terminus Island", "001", "yes", 'A: "B", C', "日本語")):
            with self.subTest(alias=alias):
                result = create_note(self.root, f"Note {index}", "pebble", alias=alias)
                metadata, body = parse_frontmatter(result.path.read_text())
                self.assertEqual(metadata["aliases"], [alias.strip()] if alias and alias.strip() else None)
                self.assertEqual(body, f"# Note {index}\n\n")

    def test_skipping_alias_preserves_template_default(self):
        self.template_field("aliases", ["Template Alias"])
        result = create_note(self.root, "Example", alias="")
        metadata, _ = parse_frontmatter(result.path.read_text())
        self.assertEqual(metadata["aliases"], ["Template Alias"])

    def test_legacy_unresolved_template_tokens_become_blank(self):
        path = self.blueprint / "Templates/Game Shard.md"
        path.write_text(path.read_text().replace("core:\n", 'core: "[[{{core}}]]"\n').replace("parent_note:\n", 'parent_note: "[[{{parent}}]]"\n'))
        result = create_note(self.root, "Subject", "shard")
        metadata, _ = parse_frontmatter(result.path.read_text())
        self.assertIsNone(metadata["core"])
        self.assertIsNone(metadata["parent_note"])

    def test_existing_notes_are_neither_read_nor_validated(self):
        database = self.live_database()
        canonical = database / "Data/Game/Terminus.md"
        canonical.write_text("Malformed canonical data\n")
        inbox = self.root / "app/Knowledge/Inbox"
        inbox.mkdir()
        capture = inbox / "Broken.md"
        capture.write_text("---\ntype: [broken\n")
        original_read = Path.read_text
        def guard_read(path, *args, **kwargs):
            if path in (canonical, capture):
                raise AssertionError("Draft creation must not inspect existing notes")
            return original_read(path, *args, **kwargs)
        with patch.object(Path, "read_text", guard_read), patch("validate_shardbase.validate_database", side_effect=AssertionError("Unexpected validation")):
            result = create_note(self.root, "Terminus", "shard")
        self.assertEqual(result.path.name, "Terminus.md")
        self.assertEqual(canonical.read_text(), "Malformed canonical data\n")
        self.assertEqual(capture.read_text(), "---\ntype: [broken\n")

    def test_canonical_validation_still_reports_unresolved_promoted_draft(self):
        database = self.live_database()
        result = create_note(self.root, "Terminus", "pebble")
        self.assertEqual(validate_database(database), [])
        shutil.copyfile(result.path, database / "Data/Game" / result.path.name)
        codes = {issue.code for issue in validate_database(database)}
        self.assertTrue({"core-reference", "parent-reference"} <= codes)

if __name__ == "__main__":
    unittest.main()

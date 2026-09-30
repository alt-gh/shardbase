import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _support import GAMES_BLUEPRINT, SCRIPTS
from note_creation import CreationError, create_note, new_id
from shardbase import Terminal, main
from validate_shardbase import NOTE_ID, parse_frontmatter, validate_database


class NoteCreationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.blueprint = self.root / "app/Blueprints/Games"
        shutil.copytree(GAMES_BLUEPRINT, self.blueprint)

    def live_database(self, name="My Games"):
        database = self.root / "app/Knowledge/Databases" / name
        shutil.copytree(self.blueprint, database)
        return database

    def assert_no_capture(self):
        self.assertFalse((self.root / "app/Knowledge/Inbox").exists())

    def metadata(self, result):
        return parse_frontmatter(result.path.read_text(encoding="utf-8"))

    def test_all_types_create_universal_inbox_drafts(self):
        for kind in ("core", "shard", "pebble"):
            with self.subTest(kind=kind):
                result = create_note(self.root, f"Example {kind}", kind)
                metadata, body = self.metadata(result)
                self.assertEqual(list(metadata), [
                    "type", "pool", "core", "parent_note", "status", "aliases", "id", "tags"
                ])
                self.assertEqual(metadata["type"], kind)
                self.assertIsNone(metadata["pool"])
                self.assertIsNone(metadata["core"])
                self.assertIsNone(metadata["parent_note"])
                self.assertEqual(metadata["status"], "draft")
                self.assertIsNone(metadata["aliases"])
                self.assertRegex(metadata["id"], NOTE_ID)
                self.assertIsNone(metadata["tags"])
                self.assertEqual(body, f"# Example {kind}\n\n")
                self.assertEqual(result.path, self.root / "app/Knowledge/Inbox" / f"Example {kind}.md")
                self.assertIsNone(result.template)
        self.assertFalse((self.root / "app/Knowledge/Inbox/Staged").exists())
        self.assertFalse((self.root / "app/Knowledge/Databases").exists())

    def test_successive_captures_receive_distinct_ids(self):
        with patch("note_creation.secrets.choice", side_effect=list("00000000001111111111")):
            first, _ = self.metadata(create_note(self.root, "First"))
            second, _ = self.metadata(create_note(self.root, "Second"))
        self.assertEqual(first["id"], "0000000000")
        self.assertEqual(second["id"], "1111111111")

    def test_id_generation_retries_for_nested_parseable_inbox_ids(self):
        nested = self.root / "app/Knowledge/Inbox/Organized"
        nested.mkdir(parents=True)
        (nested / "Existing.md").write_text("---\nid: '0000000000'\n---\n# Existing\n", encoding="utf-8")
        with patch("note_creation.secrets.choice", side_effect=list("00000000001111111111")):
            metadata, _ = self.metadata(create_note(self.root, "New"))
        self.assertEqual(metadata["id"], "1111111111")

    def test_plain_and_malformed_inbox_notes_do_not_block_capture(self):
        inbox = self.root / "app/Knowledge/Inbox"
        inbox.mkdir(parents=True)
        (inbox / "Plain.md").write_text("# Scratch\n", encoding="utf-8")
        (inbox / "Malformed.md").write_text("---\nx: [unfinished\n", encoding="utf-8")
        self.assertTrue(create_note(self.root, "Example").path.exists())

    def test_id_collision_retry_is_bounded(self):
        with patch("note_creation.secrets.choice", return_value="0"):
            with self.assertRaisesRegex(CreationError, "unused note ID"):
                new_id({"0000000000"})

    def test_games_templates_and_live_database_state_are_ignored(self):
        database = self.live_database()
        (self.blueprint / "Templates/Game.md").write_text("---\nsecret: [broken\n", encoding="utf-8")
        (database / "Templates/Game.md").unlink()
        canonical = database / "Data/Game/Broken.md"
        canonical.write_text("Malformed canonical data\n", encoding="utf-8")
        before = {path: path.read_bytes() for path in database.rglob("*") if path.is_file()}
        with patch("validate_shardbase.validate_database", side_effect=AssertionError("unexpected validation")):
            result = create_note(self.root, "Example")
        metadata, _ = self.metadata(result)
        self.assertEqual(set(metadata), {"type", "pool", "core", "parent_note", "status", "aliases", "id", "tags"})
        self.assertIsNone(metadata["pool"])
        self.assertEqual(before, {path: path.read_bytes() for path in database.rglob("*") if path.is_file()})

    def test_missing_malformed_or_symlinked_games_templates_do_not_block_capture(self):
        template = self.blueprint / "Templates/Game.md"
        template.unlink()
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "private.md"
            target.write_text("private content", encoding="utf-8")
            template.symlink_to(target)
            self.assertTrue(create_note(self.root, "Example").path.exists())

    def test_existing_nested_capture_is_preserved(self):
        nested = self.root / "app/Knowledge/Inbox/Organized"
        nested.mkdir(parents=True)
        capture = nested / "Example.md"
        capture.write_text("User-authored content\n", encoding="utf-8")
        result = create_note(self.root, "Example")
        self.assertEqual(result.path, nested.parent / "Example.md")
        self.assertEqual(capture.read_text(encoding="utf-8"), "User-authored content\n")

    def test_portable_names_preserve_display_title_and_yaml_safety(self):
        cases = (("Example: Game #1", "Example Game 1.md"), ('Game [Remastered] "Edition"', "Game Remastered Edition.md"),
                 ("CON", "_CON.md"), ("Game. .", "Game.md"), ("Café 🎮", "Café 🎮.md"),
                 ("on", "on.md"), ("../Outside", ".. Outside.md"))
        for index, (title, filename) in enumerate(cases):
            with self.subTest(title=title):
                result = create_note(self.root, title, alias='A: "B", C' if index == 0 else None)
                metadata, body = self.metadata(result)
                self.assertEqual(result.path.name, filename)
                self.assertEqual(body, f"# {title}\n\n")
                if index == 0:
                    self.assertEqual(metadata["aliases"], ['A: "B", C'])

    def test_optional_alias_is_a_yaml_string_list_or_blank(self):
        for index, alias in enumerate((None, "", "   ", "Example Alias", "001", "yes", "日本語")):
            with self.subTest(alias=alias):
                result = create_note(self.root, f"Note {index}", "pebble", alias)
                metadata, body = self.metadata(result)
                self.assertEqual(metadata["aliases"], [alias.strip()] if alias and alias.strip() else None)
                self.assertEqual(body, f"# Note {index}\n\n")
                if alias and alias.strip():
                    self.assertIn("aliases:\n  - ", result.path.read_text(encoding="utf-8"))

    def test_empty_multiline_and_invalid_types_are_refused(self):
        for title in ("", "   ", "...", "[]/#", "Title\nInjected", "Title\x00Injected", "Title\u2028Injected"):
            with self.subTest(title=title), self.assertRaises(CreationError):
                create_note(self.root, title)
        with self.assertRaisesRegex(CreationError, "core, shard, or pebble"):
            create_note(self.root, "Example", "other")
        self.assert_no_capture()

    def test_existing_file_and_normalized_collisions_never_overwritten(self):
        first = create_note(self.root, "Game: One")
        first.path.write_text("User-edited content", encoding="utf-8")
        for title in ("Game: One", "Game One", "game one"):
            with self.assertRaisesRegex(CreationError, "already uses"):
                create_note(self.root, title)
            self.assertEqual(first.path.read_text(encoding="utf-8"), "User-edited content")
        self.assertEqual(list(first.path.parent.iterdir()), [first.path])

    def test_unicode_equivalent_collisions_are_refused(self):
        create_note(self.root, "Café")
        with self.assertRaises(CreationError):
            create_note(self.root, "Cafe\u0301")

    def test_symlink_boundaries_are_refused(self):
        for relative in ("app/Knowledge", "app/Knowledge/Inbox"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as outside:
                path = self.root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(outside, target_is_directory=True)
                with self.assertRaises(CreationError):
                    create_note(self.root, "Example")
                self.assertEqual(list(Path(outside).iterdir()), [])
                path.unlink()

    def test_dangling_destination_symlink_is_never_followed(self):
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
                path.write_text("Competing content", encoding="utf-8")
            return original_open(path, mode, *args, **kwargs)

        with patch.object(Path, "open", competing_open), self.assertRaises(FileExistsError):
            create_note(self.root, "Example")
        self.assertEqual((self.root / "app/Knowledge/Inbox/Example.md").read_text(encoding="utf-8"), "Competing content")

    def test_prompts_ask_only_for_title_type_and_alias(self):
        with patch("builtins.input", side_effect=["Example", "invalid", "1", ""]) as prompts, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["new", "--root", str(self.root)]), 0)
        self.assertEqual(prompts.call_count, 4)
        rendered = output.getvalue()
        self.assertIn("Choose 1", rendered)
        self.assertIn("Saved to Inbox", rendered)
        for absent in ("Note intent", "Live database", "Parent note", "Pool", "Collection", "Template"):
            self.assertNotIn(absent, rendered)

    def test_cancelled_prompts_write_nothing(self):
        for error in (EOFError(), KeyboardInterrupt()):
            with patch("builtins.input", side_effect=["Example", error]), contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["new", "--root", str(self.root)]), 130)
            self.assert_no_capture()

    def test_subprocess_help_routes_and_removed_flags(self):
        command = [sys.executable, "-B", str(SCRIPTS / "shardbase.py")]
        for route, title in ((["create", "new"], "Grouped"), (["new"], "Alias")):
            help_result = subprocess.run(command + route + ["--help"], capture_output=True, text=True)
            self.assertEqual(help_result.returncode, 0)
            self.assertIn("app/Knowledge/Inbox/", help_result.stdout)
            for option in ("--intent", "--database", "--template", "--pool", "--core", "--parent", "--collection"):
                self.assertNotIn(option, help_result.stdout)
            args = route + ["--root", str(self.root), "--title", title, "--type", "core", "--alias", ""]
            created = subprocess.run(command + args, capture_output=True, text=True)
            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertTrue((self.root / "app/Knowledge/Inbox" / f"{title}.md").is_file())
        for route in (["create", "new"], ["new"]):
            for option, value in (("--intent", "database"), ("--database", "games"), ("--template", "Game.md"),
                                  ("--pool", "Games"), ("--core", "Example"), ("--parent", "Example"),
                                  ("--collection", "Game")):
                result = subprocess.run(command + route + ["--root", str(self.root), "--title", "Rejected",
                                                           "--type", "core", "--alias", "", option, value],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn(f"unrecognized arguments: {option}", result.stderr)
                self.assertFalse((self.root / "app/Knowledge/Inbox/Rejected.md").exists())
        self.assertEqual(list(self.root.rglob("__pycache__")), [])

    def test_terminal_color_is_optional_and_control_characters_are_inert(self):
        with patch("sys.stdout.isatty", return_value=True), patch.dict("os.environ", {"TERM": "xterm"}, clear=True):
            self.assertIn("\033[", Terminal().style("Title"))
            self.assertNotIn("\033[", Terminal(no_color=True).style("Title"))
            with patch.dict("os.environ", {"NO_COLOR": ""}):
                self.assertNotIn("\033[", Terminal().style("Title"))
        with patch("sys.stdout.isatty", return_value=False):
            self.assertEqual(Terminal().style("Title\033[2J"), "Title [2J")

    def test_canonical_validation_reports_unresolved_manually_promoted_capture(self):
        database = self.live_database()
        result = create_note(self.root, "Example Detail", "pebble")
        self.assertEqual(validate_database(database), [])
        shutil.copyfile(result.path, database / "Data/Game" / result.path.name)
        codes = {issue.code for issue in validate_database(database)}
        self.assertTrue({"core-reference", "parent-reference"} <= codes)


if __name__ == "__main__":
    unittest.main()

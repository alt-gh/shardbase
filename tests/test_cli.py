"""Proof of discoverable commands and existing CLI behavior."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _support import FIXTURES, GAMES_BLUEPRINT, SCRIPTS


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "Example Instance"
        self.root.mkdir()
        shutil.copytree(GAMES_BLUEPRINT, self.root / "app/Blueprints/Games")

    def cli(self, *args, without_dependencies=False):
        command = [sys.executable, "-B"]
        if without_dependencies:
            command.append("-S")
        return subprocess.run(command + [str(SCRIPTS / "shardbase.py"), *args],
                              input="", capture_output=True, text=True, cwd=self.root)

    def test_command_catalog_and_help_work_without_dependencies(self):
        for arguments in ((), ("commands",), ("--help",), ("help",), ("help", "create", "new"),
                          ("create",), ("create", "new", "--help"), ("validate", "--help"),
                          ("help", "create", "new", "database"), ("create", "new", "database", "--help"),
                          ("backup", "--help"), ("restore", "--help"), ("help", "backup"), ("help", "restore")):
            with self.subTest(arguments=arguments):
                result = self.cli(*arguments, without_dependencies=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("shardbase", result.stdout)
        result = self.cli("commands", without_dependencies=True)
        for command in ("create", "create new", "create new database", "new", "validate", "backup", "restore", "commands", "help"):
            self.assertIn(f"shardbase {command}", result.stdout)
        self.assertIn("Alias for create new", result.stdout)

    def test_help_topics_share_the_actual_command_parser(self):
        for route in (("create", "new"), ("create", "new", "database"), ("new",), ("validate",), ("backup",), ("restore",), ("commands",)):
            with self.subTest(route=route):
                direct = self.cli(*route, "--help")
                topic = self.cli("help", *route)
                self.assertEqual(direct.stdout, topic.stdout)
                self.assertEqual(topic.returncode, 0)

    def test_invalid_command_or_help_topic_exits_cleanly(self):
        for route in (("missing",), ("create", "missing"), ("help", "missing")):
            result = self.cli(*route)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)

    def test_grouped_creation_and_legacy_alias_preserve_intents(self):
        database = self.root / "app/Knowledge/Databases/Games"
        shutil.copytree(self.root / "app/Blueprints/Games", database)
        for route, title, intent in ((("create", "new"), "Example Game", "database"),
                                     (("new",), "Temporary idea", "inbox")):
            args = [*route, "--root", str(self.root), "--title", title, "--type", "core",
                    "--alias", "", "--intent", intent]
            if intent == "database":
                args += ["--database", "games"]
            result = self.cli(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = database / "Data/Game" / title / f"{title}.md" if intent == "database" else self.root / "app/Knowledge/Inbox" / f"{title}.md"
            self.assertTrue(expected.is_file())
        self.assertEqual(list(self.root.rglob("__pycache__")), [])

    def test_validate_command_checks_selected_instance_and_returns_failures(self):
        database = self.root / "app/Knowledge/Databases/Example Database"
        shutil.copytree(FIXTURES / "valid-database", database)
        before = {path: path.read_bytes() for path in database.rglob("*") if path.is_file()}
        for arguments in (("--root", str(self.root)), (str(database),)):
            result = self.cli("validate", *arguments)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("structural checks passed", result.stdout)
        self.assertEqual(before, {path: path.read_bytes() for path in database.rglob("*") if path.is_file()})
        (database / "Data/Game/Broken.md").write_text("# Missing metadata\n")
        result = self.cli("validate", "--root", str(self.root))
        self.assertEqual(result.returncode, 1)
        self.assertIn("structural-frontmatter", result.stdout)

    def test_validate_distinguishes_empty_instance_from_invalid_root(self):
        empty = self.cli("validate", "--root", str(self.root))
        self.assertEqual(empty.returncode, 0)
        self.assertIn("No databases found", empty.stdout)
        invalid = self.cli("validate", "--root", str(self.root / "Missing"))
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("containing app/", invalid.stderr)


if __name__ == "__main__":
    unittest.main()

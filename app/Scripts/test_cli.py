"""Proof of discoverable commands and an external-runtime launcher."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from install_cli import external_path, install


SCRIPTS = Path(__file__).resolve().parent
PROJECT = SCRIPTS.parents[1]


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "Example Instance"
        self.root.mkdir()
        shutil.copytree(PROJECT / "app/Blueprints/Games", self.root / "app/Blueprints/Games")

    def cli(self, *args, without_dependencies=False):
        command = [sys.executable, "-B"]
        if without_dependencies:
            command.append("-S")
        return subprocess.run(command + [str(SCRIPTS / "shardbase.py"), *args],
                              input="", capture_output=True, text=True, cwd=self.root)

    def test_command_catalog_and_help_work_without_dependencies(self):
        for arguments in ((), ("commands",), ("--help",), ("help",), ("help", "create", "new"),
                          ("create",), ("create", "new", "--help"), ("validate", "--help"),
                          ("help", "create", "new", "database"), ("create", "new", "database", "--help")):
            with self.subTest(arguments=arguments):
                result = self.cli(*arguments, without_dependencies=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("shardbase", result.stdout)
        result = self.cli("commands", without_dependencies=True)
        for command in ("create", "create new", "create new database", "new", "validate", "commands", "help"):
            self.assertIn(f"shardbase {command}", result.stdout)
        self.assertIn("Alias for create new", result.stdout)

    def test_help_topics_share_the_actual_command_parser(self):
        for route in (("create", "new"), ("create", "new", "database"), ("new",), ("validate",), ("commands",)):
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
        for route, title, intent in ((("create", "new"), "Example Game", "database"),
                                     (("new",), "Temporary idea", "inbox")):
            args = [*route, "--root", str(self.root), "--title", title, "--type", "core",
                    "--alias", "", "--intent", intent]
            if intent == "database":
                args += ["--database", "games"]
            result = self.cli(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((self.root / "app/Knowledge/Inbox" / f"{title}.md").is_file())
        self.assertFalse((self.root / "app/Knowledge/Databases").exists())
        self.assertEqual(list(self.root.rglob("__pycache__")), [])

    def test_validate_command_checks_selected_instance_and_returns_failures(self):
        database = self.root / "app/Knowledge/Databases/Example Database"
        shutil.copytree(SCRIPTS / "fixtures/valid-database", database)
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


@unittest.skipUnless(os.name == "posix", "POSIX launcher")
class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def runtime(self):
        runtime = self.root / "runtime"
        (runtime / "bin").mkdir(parents=True)
        (runtime / "bin/python").write_text("test interpreter placeholder")
        (runtime / "pyvenv.cfg").write_text("test environment placeholder")
        return runtime

    def test_project_runtime_and_launcher_locations_are_rejected_before_work(self):
        for runtime, bin_dir in ((PROJECT / ".venv", self.root / "bin"),
                                 (self.root / "runtime", PROJECT / "bin")):
            with patch("install_cli.subprocess.run") as run, self.assertRaisesRegex(ValueError, "outside"):
                install(runtime, bin_dir)
            run.assert_not_called()

    def test_symlink_into_project_and_other_vaults_are_rejected(self):
        link = self.root / "project-link"
        link.symlink_to(PROJECT, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "outside"):
            external_path(link / ".venv", "Runtime")
        vault = self.root / "Another Vault"
        (vault / ".obsidian").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "outside"):
            external_path(vault / ".venv", "Runtime")

    def test_temporary_directory_inside_project_is_rejected(self):
        with patch("install_cli.tempfile.gettempdir", return_value=str(PROJECT / "tmp")), patch("install_cli.subprocess.run") as run:
            with self.assertRaisesRegex(ValueError, "Temporary directory"):
                install(self.root / "runtime", self.root / "bin")
        run.assert_not_called()

    def test_existing_unrelated_runtime_and_launcher_are_preserved(self):
        runtime = self.root / "unrelated"
        runtime.mkdir()
        original = runtime / "User.md"
        original.write_text("Preserve this")
        with self.assertRaisesRegex(ValueError, "already exists"):
            install(runtime, self.root / "bin")
        self.assertEqual(original.read_text(), "Preserve this")
        launcher = self.root / "bin/shardbase"
        launcher.parent.mkdir()
        launcher.write_text("Unrelated command")
        with self.assertRaisesRegex(ValueError, "launcher differs"):
            install(self.root / "new-runtime", launcher.parent)
        self.assertEqual(launcher.read_text(), "Unrelated command")

    def test_dependency_failure_does_not_install_a_launcher(self):
        with patch("install_cli.subprocess.run", side_effect=subprocess.CalledProcessError(1, "pip")):
            with self.assertRaises(subprocess.CalledProcessError):
                install(self.runtime(), self.root / "bin")
        self.assertFalse((self.root / "bin/shardbase").exists())

    def test_launcher_created_during_dependency_setup_is_preserved(self):
        launcher = self.root / "bin/shardbase"

        def competing_install(*args, **kwargs):
            launcher.parent.mkdir()
            launcher.write_text("Another command")
            launcher.chmod(0o600)

        with patch("install_cli.subprocess.run", side_effect=competing_install):
            with self.assertRaisesRegex(ValueError, "launcher differs"):
                install(self.runtime(), launcher.parent)
        self.assertEqual(launcher.read_text(), "Another command")
        self.assertEqual(launcher.stat().st_mode & 0o777, 0o600)

    def test_install_is_repeatable_and_does_not_create_project_runtime(self):
        runtime = self.runtime()
        with patch("install_cli.subprocess.run") as run:
            launcher = install(runtime, self.root / "bin")
            before = launcher.read_bytes()
            self.assertEqual(install(runtime, self.root / "bin").read_bytes(), before)
        command = run.call_args.args[0]
        self.assertIn("--isolated", command)
        self.assertIn("--no-cache-dir", command)
        self.assertIn("--no-compile", command)
        self.assertEqual(run.call_args.kwargs["cwd"], runtime)
        self.assertTrue(os.access(launcher, os.X_OK))

    def test_launcher_preserves_arguments_and_quoted_paths(self):
        runtime = self.runtime().rename(self.root / "runtime with 'quotes' and $characters")
        bin_dir = self.root / "bin with 'quotes' and $characters"
        with patch("install_cli.subprocess.run"):
            launcher = install(runtime, bin_dir)
        # Use an actual interpreter after isolating dependency installation.
        python = runtime / "bin/python"
        python.unlink()
        python.symlink_to(sys.executable)
        result = subprocess.run([str(launcher), "help", "create", "new"],
                                capture_output=True, text=True, cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--intent", result.stdout)


if __name__ == "__main__":
    unittest.main()

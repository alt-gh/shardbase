"""Synthetic, network-free coverage of bootstrap safety and native launchers."""

import ast
import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PureWindowsPath
from unittest.mock import patch

from _support import ROOT

# _support makes the non-packaged scripts importable.
# isort: split
import bootstrap_support as support
import install_cli


def snapshot(root):
    return {path.relative_to(root): path.read_bytes() if path.is_file() else None
            for path in root.rglob("*")}


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "Example Instance"
        self.root.mkdir()
        for marker in ("app/Scripts/shardbase.py", "app/Scripts/requirements.txt", support.SPECIFICATION):
            path = self.root / marker
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Synthetic framework marker\n", encoding="utf-8")
        self.runtime = self.base / "runtime"
        self.bin_dir = self.base / "bin"
        self.launcher = self.bin_dir / ("shardbase.cmd" if os.name == "nt" else "shardbase")
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        stack.enter_context(contextlib.redirect_stdout(self.stdout))
        stack.enter_context(contextlib.redirect_stderr(self.stderr))
        self.run = stack.enter_context(patch.object(support.subprocess, "run", side_effect=self.fake_run))
        self.version = [3, 10, 0]
        self.failure = None
        self.on_pip = None

    def make_runtime(self):
        interpreter = support.venv_python(self.runtime, os.name)
        interpreter.parent.mkdir(parents=True, exist_ok=True)
        interpreter.write_text("Synthetic interpreter")
        (self.runtime / "pyvenv.cfg").write_text("Synthetic venv")

    def fake_run(self, command, **kwargs):
        if "venv" in command:
            if self.failure == "venv":
                self.runtime.mkdir()
                raise subprocess.CalledProcessError(1, command)
            self.make_runtime()
        if "-c" in command:
            if self.failure == "interpreter":
                raise OSError("Cannot execute")
            return subprocess.CompletedProcess(command, 0, json.dumps([self.version, str(self.runtime)]))
        if "pip" in command:
            if self.on_pip:
                self.on_pip()
            if self.failure == "pip":
                raise subprocess.CalledProcessError(1, command)
        if command[-1] == "commands" and self.failure == "smoke":
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0, "")

    def install(self, root=None):
        return support.install(root or self.root, self.runtime, self.bin_dir)

    def setup(self):
        return support.setup_main(self.root, ["--runtime", str(self.runtime), "--bin-dir", str(self.bin_dir)], bootstrap=True)

    def symlink(self, path, target, directory=False):
        try:
            path.symlink_to(target, target_is_directory=directory)
        except OSError as error:
            self.skipTest(f"Symlinks unavailable: {error}")

    def test_missing_framework_markers_fail_before_work(self):
        for marker in ("app/Scripts/shardbase.py", "app/Scripts/requirements.txt", support.SPECIFICATION):
            path = self.root / marker
            data = path.read_bytes()
            path.unlink()
            with self.subTest(marker=marker), self.assertRaisesRegex(support.SetupError, "Expected a ShardBase"):
                self.install()
            path.write_bytes(data)
        self.run.assert_not_called()
        self.assertFalse(self.runtime.exists())

    def test_fresh_instance_without_knowledge_is_accepted_and_unchanged(self):
        before = snapshot(self.root)
        self.assertEqual(self.setup(), 0)
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse((self.root / "app/Knowledge").exists())
        self.assertIn("Private instance mode", self.stdout.getvalue())

    def test_existing_synthetic_knowledge_is_untouched(self):
        note = self.root / "app/Knowledge/Inbox/Example.md"
        note.parent.mkdir(parents=True)
        note.write_text("User-owned synthetic content\n")
        before = snapshot(self.root)
        self.install()
        self.assertEqual(snapshot(self.root), before)

    def test_current_instance_runtime_and_bin_are_rejected(self):
        for runtime, bin_dir in ((self.root / ".venv", self.bin_dir), (self.runtime, self.root / "bin")):
            with self.subTest(runtime=runtime), self.assertRaisesRegex(support.SetupError, "outside"):
                support.install(self.root, runtime, bin_dir)
        self.run.assert_not_called()

    def test_other_instance_and_obsidian_vault_are_rejected(self):
        for marker in (support.SPECIFICATION, ".obsidian/settings"):
            vault = self.base / ("vault" if marker.startswith(".obsidian") else "instance")
            file = vault / marker
            file.parent.mkdir(parents=True)
            file.touch()
            with self.subTest(marker=marker), self.assertRaisesRegex(support.SetupError, "outside every"):
                support.external_path(vault / "runtime", "Runtime", self.root)
        self.run.assert_not_called()

    def test_symlink_into_instance_is_rejected(self):
        link = self.base / "linked"
        self.symlink(link, self.root, True)
        with self.assertRaisesRegex(support.SetupError, "outside"):
            support.install(self.root, link / ".venv", self.bin_dir)
        self.run.assert_not_called()

    def test_protected_temporary_directory_is_rejected(self):
        with patch.object(support.tempfile, "gettempdir", return_value=str(self.root / "tmp")):
            with self.assertRaisesRegex(support.SetupError, "Temporary directory"):
                self.install()
        self.run.assert_not_called()

    def test_platform_defaults_and_windows_fallback(self):
        home = self.base / "home"
        self.assertEqual(support.default_paths("posix", {}, home),
                         (home / ".local/share/shardbase/venv", home / ".local/bin"))
        local = self.base / "Local Data"
        self.assertEqual(support.default_paths("nt", {"LOCALAPPDATA": str(local)}, home),
                         (local / "ShardBase/venv", local / "ShardBase/bin"))
        for environment in ({}, {"LOCALAPPDATA": ""}):
            self.assertEqual(support.default_paths("nt", environment, home),
                             (home / "AppData/Local/ShardBase/venv", home / "AppData/Local/ShardBase/bin"))

    def test_platform_interpreter_paths(self):
        self.assertEqual(support.venv_python(self.runtime, "posix"), self.runtime / "bin/python")
        self.assertEqual(support.venv_python(self.runtime, "nt"), self.runtime / "Scripts/python.exe")

    def test_new_runtime_creation_and_reuse(self):
        self.install()
        self.assertEqual(sum("venv" in call.args[0] for call in self.run.call_args_list), 1)
        self.run.reset_mock()
        self.install()
        self.assertFalse(any("venv" in call.args[0] for call in self.run.call_args_list))
        self.assertTrue(any("-c" in call.args[0] for call in self.run.call_args_list))

    def test_invalid_runtime_preserved(self):
        self.runtime.mkdir()
        (self.runtime / "personal.txt").write_text("Keep this")
        before = snapshot(self.runtime)
        with self.assertRaisesRegex(support.SetupError, "already exists"):
            self.install()
        self.assertEqual(snapshot(self.runtime), before)
        self.run.assert_not_called()

    def test_incomplete_runtime_preserved(self):
        self.make_runtime()
        support.venv_python(self.runtime, os.name).unlink()
        before = snapshot(self.runtime)
        with self.assertRaisesRegex(support.SetupError, "usable virtual"):
            self.install()
        self.assertEqual(snapshot(self.runtime), before)
        self.run.assert_not_called()

    def test_unsupported_runtime_preserved(self):
        self.make_runtime()
        self.version = [3, 9, 20]
        before = snapshot(self.runtime)
        with self.assertRaisesRegex(support.SetupError, "Python 3.9.20"):
            self.install()
        self.assertEqual(snapshot(self.runtime), before)
        self.assertFalse(self.launcher.exists())
        self.assertFalse(any("pip" in call.args[0] for call in self.run.call_args_list))

    def test_future_runtime_version_has_no_upper_limit(self):
        self.version = [4, 0, 0]
        self.install()

    def test_unexecutable_runtime_has_clean_error(self):
        self.failure = "interpreter"
        self.assertEqual(self.setup(), 1)
        self.assertIn("Runtime interpreter check", self.stderr.getvalue())
        self.assertNotIn("Traceback", self.stderr.getvalue())

    def test_malformed_runtime_probe_is_rejected(self):
        self.make_runtime()
        self.run.side_effect = None
        for stdout in ("invalid", "null", "[]", '["3.10", "/tmp"]', '[[3, 10, 0], 42]'):
            self.run.return_value = subprocess.CompletedProcess([], 0, stdout)
            with self.subTest(stdout=stdout), self.assertRaisesRegex(support.SetupError, "invalid version"):
                self.install()

    def test_interpreter_from_wrong_environment_is_rejected(self):
        self.make_runtime()
        self.run.side_effect = None
        self.run.return_value = subprocess.CompletedProcess([], 0, json.dumps([[3, 10, 0], str(self.base)]))
        with self.assertRaisesRegex(support.SetupError, "does not belong"):
            self.install()

    def test_failed_venv_creation_preserves_partial_runtime(self):
        self.failure = "venv"
        self.assertEqual(self.setup(), 1)
        self.assertTrue(self.runtime.is_dir())
        self.assertFalse(self.launcher.exists())
        self.assertIn("venv/ensurepip", self.stderr.getvalue())

    def test_pip_and_smoke_commands_are_hardened_and_external(self):
        environment = dict(os.environ)
        self.install()
        calls = self.run.call_args_list
        pip = next(call for call in calls if "pip" in call.args[0])
        python = str(support.venv_python(self.runtime, os.name))
        self.assertEqual(pip.args[0], [python, "-B", "-m", "pip", "--isolated", "install",
                                     "--no-cache-dir", "--no-compile", "--disable-pip-version-check",
                                     "-r", str(self.root / "app/Scripts/requirements.txt")])
        self.assertEqual(pip.kwargs["cwd"], self.runtime)
        for call in calls:
            self.assertEqual(call.kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1")
            for key in ("TMP", "TEMP", "TMPDIR"):
                self.assertFalse(Path(call.kwargs["env"][key]).is_relative_to(self.root))
            self.assertNotEqual(call.args[0][0], "git")
        self.assertEqual(calls[-1].args[0], [python, "-B", str(self.root / "app/Scripts/shardbase.py"), "commands"])
        self.assertEqual(dict(os.environ), environment)
        self.assertIn("network resources", self.stdout.getvalue())

    def test_dependency_failure_does_not_publish_launcher(self):
        self.failure = "pip"
        self.assertEqual(self.setup(), 1)
        self.assertFalse(self.launcher.exists())
        self.assertIn("Dependency installation", self.stderr.getvalue())

    def test_managed_launcher_is_unchanged_when_new_dependencies_fail(self):
        self.install()
        before = self.launcher.read_bytes()
        other = self.base / "New Instance"
        shutil.copytree(self.root, other)
        self.failure = "pip"
        with self.assertRaisesRegex(support.SetupError, "Dependency"):
            self.install(other)
        self.assertEqual(self.launcher.read_bytes(), before)

    def test_exact_managed_rerun_is_idempotent(self):
        self.install()
        before = self.launcher.read_bytes(), self.launcher.stat().st_mtime_ns
        self.install()
        self.assertEqual((self.launcher.read_bytes(), self.launcher.stat().st_mtime_ns), before)
        if os.name == "posix":
            self.assertTrue(os.access(self.launcher, os.X_OK))

    def test_managed_retarget_and_legacy_posix_upgrade(self):
        self.install()
        if os.name == "posix":
            self.launcher.write_text(self.launcher.read_text().replace(support.POSIX_HEADER, support.LEGACY_HEADER))
        other = self.base / "New Instance"
        shutil.copytree(self.root, other)
        before = snapshot(self.root)
        self.install(other)
        self.assertIn(str(other), self.launcher.read_text())
        self.assertIn(support.MARKER, self.launcher.read_text())
        self.assertNotIn(str(self.root), self.launcher.read_text())
        self.assertEqual(snapshot(self.root), before)

    def test_unrecognized_launcher_preserved_before_runtime_creation(self):
        self.bin_dir.mkdir()
        for contents in ("Unrelated command", support.POSIX_HEADER + "echo surprise\n", "\ufffd"):
            self.launcher.write_text(contents, encoding="utf-8")
            before = self.launcher.read_bytes()
            with self.subTest(contents=contents), self.assertRaises(support.SetupError):
                self.install()
            self.assertEqual(self.launcher.read_bytes(), before)
        self.run.assert_not_called()
        self.assertFalse(self.runtime.exists())

    def test_non_utf8_launcher_preserved(self):
        self.bin_dir.mkdir()
        self.launcher.write_bytes(b"\xff\xfe")
        with self.assertRaisesRegex(support.SetupError, "Unrecognized"):
            self.install()
        self.assertEqual(self.launcher.read_bytes(), b"\xff\xfe")

    def test_directory_launcher_preserved(self):
        self.launcher.mkdir(parents=True)
        with self.assertRaisesRegex(support.SetupError, "Unexpected"):
            self.install()
        self.assertTrue(self.launcher.is_dir())
        self.run.assert_not_called()

    def test_symlink_launcher_preserved(self):
        self.bin_dir.mkdir()
        target = self.base / "unrelated"
        target.write_text("Keep")
        self.symlink(self.launcher, target)
        with self.assertRaisesRegex(support.SetupError, "Unexpected"):
            self.install()
        self.assertTrue(self.launcher.is_symlink())
        self.assertEqual(target.read_text(), "Keep")

    @unittest.skipUnless(os.name == "posix", "POSIX FIFO")
    def test_special_file_launcher_is_not_opened(self):
        self.bin_dir.mkdir()
        os.mkfifo(self.launcher)
        with self.assertRaisesRegex(support.SetupError, "Unexpected"):
            self.install()

    def test_competing_launcher_during_pip_is_preserved(self):
        def competitor():
            self.bin_dir.mkdir(exist_ok=True)
            self.launcher.write_text("Competing command")
        self.on_pip = competitor
        with self.assertRaisesRegex(support.SetupError, "launcher differs"):
            self.install()
        self.assertEqual(self.launcher.read_text(), "Competing command")

    def test_competing_managed_launcher_during_pip_is_preserved(self):
        self.install()
        other = self.base / "Other Instance"
        contents = support.render_launcher(support.venv_python(self.runtime, os.name),
                                           other / "app/Scripts/shardbase.py", os.name)
        self.on_pip = lambda: self.launcher.write_text(contents)
        with self.assertRaisesRegex(support.SetupError, "changed during"):
            self.install()
        self.assertEqual(self.launcher.read_text(), contents)

    def test_final_publication_rechecks_and_preserves_competitor(self):
        original_mkstemp = support.tempfile.mkstemp
        def compete(*args, **kwargs):
            result = original_mkstemp(*args, **kwargs)
            self.launcher.write_text("Late competitor")
            return result
        with patch.object(support.tempfile, "mkstemp", side_effect=compete):
            with self.assertRaisesRegex(support.SetupError, "launcher differs"):
                self.install()
        self.assertEqual(self.launcher.read_text(), "Late competitor")
        self.assertEqual(list(self.bin_dir.glob(".shardbase-*")), [])

    def test_publication_failure_is_clean_and_staging_is_removed(self):
        with patch.object(support.os, "link", side_effect=OSError("Write denied")):
            self.assertEqual(self.setup(), 1)
        self.assertIn("Write denied", self.stderr.getvalue())
        self.assertFalse(self.launcher.exists())
        self.assertEqual(list(self.bin_dir.glob(".shardbase-*")), [])

    def test_smoke_failure_is_bootstrap_failure(self):
        self.failure = "smoke"
        self.assertEqual(self.setup(), 1)
        self.assertIn("CLI smoke check", self.stderr.getvalue())
        self.assertNotIn("tooling is ready", self.stdout.getvalue())

    def test_git_marker_file_or_directory_reporting(self):
        git = self.root / ".git"
        for directory in (False, True):
            if directory:
                git.mkdir()
            else:
                git.write_text("gitdir: elsewhere")
            self.stdout.seek(0)
            self.stdout.truncate()
            self.assertEqual(self.setup(), 0)
            self.assertIn("Git-managed/development", self.stdout.getvalue())
            self.assertNotIn("locally isolated", self.stdout.getvalue())
            git.rmdir() if directory else git.unlink()

    def test_parent_git_is_not_consulted(self):
        (self.base / ".git").mkdir()
        self.assertEqual(self.setup(), 0)
        self.assertIn("Private instance mode", self.stdout.getvalue())

    def test_path_normalization_and_guidance(self):
        self.assertTrue(support.launcher_on_path(self.bin_dir, "posix", {"PATH": str(self.bin_dir / "../bin")}))
        self.assertTrue(support.launcher_on_path(PureWindowsPath("C:/Tools/Bin"), "nt",
                                               {"PATH": '"c:\\TOOLS\\bin";C:\\other'}))
        self.assertFalse(support.launcher_on_path(self.bin_dir, "posix", {"PATH": ""}))
        support.report_completion(self.root, self.runtime, self.launcher, os.name, {"PATH": str(self.bin_dir)})
        self.assertIn("is on PATH", self.stdout.getvalue())
        self.stdout.seek(0)
        self.stdout.truncate()
        for platform in ("posix", "nt"):
            support.report_completion(self.root, self.runtime, self.launcher, platform, {"PATH": ""})
        output = self.stdout.getvalue()
        self.assertIn("is not on PATH", output)
        self.assertIn("export PATH=", output)
        self.assertIn("PowerShell: $env:Path", output)

    def test_compatibility_wrapper_delegates(self):
        with patch.object(support, "setup_main", return_value=0) as setup:
            self.assertEqual(install_cli.main(["--runtime", str(self.runtime)]), 0)
        setup.assert_called_once_with(ROOT, ["--runtime", str(self.runtime)])


class LauncherFormatTests(unittest.TestCase):
    def test_posix_quoting_and_full_format_recognition(self):
        python = "/external/quotes' $money & stuff/bin/python"
        script = "/instance/quotes' $money & stuff/app/Scripts/shardbase.py"
        contents = support.render_launcher(python, script, "posix")
        self.assertEqual(support.launcher_targets(contents, "posix"), (python, script))
        self.assertEqual(support.launcher_targets(contents.replace(support.POSIX_HEADER, support.LEGACY_HEADER), "posix"), (python, script))
        self.assertTrue(support.managed_launcher(contents, "posix"))
        self.assertTrue(support.managed_launcher(contents.replace(support.POSIX_HEADER, support.LEGACY_HEADER), "posix"))
        for altered in (contents + "echo changed\n", contents.replace(": 1", ": 2"),
                        contents.replace('"$@"', "$@"), contents.replace(" -B ", " ")):
            self.assertFalse(support.managed_launcher(altered, "posix"))
            self.assertIsNone(support.launcher_targets(altered, "posix"))

    def test_windows_escaping_and_full_format_recognition(self):
        contents = support.render_launcher(r"C:\Runtime %PATH% ! ^ & (test)\Scripts\python.exe",
                                           r"C:\Instance %HOME% ! ^ & (test)\app\Scripts\shardbase.py", "nt")
        self.assertIn("%%PATH%%", contents)
        self.assertIn("DisableDelayedExpansion", contents)
        self.assertIn(" %*\nexit /b %errorlevel%", contents)
        self.assertTrue(support.managed_launcher(contents, "nt"))
        self.assertEqual(support.launcher_targets(contents, "nt"),
                         (r"C:\Runtime %PATH% ! ^ & (test)\Scripts\python.exe",
                          r"C:\Instance %HOME% ! ^ & (test)\app\Scripts\shardbase.py"))
        for altered in (contents + "echo changed\n", contents.replace(": 1", ": 2"),
                        contents.replace("%%PATH%%", "%PATH%"), contents.replace(" %*", "")):
            self.assertFalse(support.managed_launcher(altered, "nt"))
            self.assertIsNone(support.launcher_targets(altered, "nt"))

    def test_unsafe_embedded_paths_fail(self):
        for platform in ("posix", "nt"):
            with self.assertRaises(support.SetupError):
                support.render_launcher("/bad\npath", "/instance/app/Scripts/shardbase.py", platform)
        with self.assertRaises(support.SetupError):
            support.render_launcher('C:\\bad"path', "C:\\instance", "nt")

    def test_native_argument_forwarding_spaces_metacharacters_and_exit_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            special = "spaces ' & ^ ! %SHARDBASE_TEST% (example)"
            if os.name == "posix":
                special += " $value"
            root = base / special
            script = root / "app/Scripts/shardbase.py"
            script.parent.mkdir(parents=True)
            script.write_text("import json,sys\nprint(json.dumps(sys.argv[1:]))\nsys.exit(7)\n")
            runtime = base / ("runtime " + special)
            # A real venv avoids Windows executable relocation/DLL assumptions.
            subprocess.run([sys.executable, "-B", "-m", "venv", "--without-pip", str(runtime)], check=True,
                           cwd=base, capture_output=True)
            launcher = base / ("shardbase.cmd" if os.name == "nt" else "shardbase")
            launcher.write_text(support.render_launcher(support.venv_python(runtime, os.name), script, os.name),
                                encoding="utf-8", newline="\n")
            launcher.chmod(0o755)
            arguments = ["help", "two words", "", "a&b", "bang!", "(group)", "caret^"]
            if os.name == "nt":
                # Pass cmd its native command string; list2cmdline's C-runtime
                # quoting rules do not describe cmd's /c shell grammar.
                quoted = " ".join('"' + arg + '"' for arg in arguments)
                shell = subprocess.list2cmdline([os.environ.get("COMSPEC", "cmd.exe")])
                command = f'{shell} /d /v:off /s /c ""{launcher}" {quoted}"'
            else:
                arguments += ["literal'$value", "percent%text"]
                command = [str(launcher), *arguments]
            result = subprocess.run(command, cwd=base, text=True, capture_output=True,
                                    env=dict(os.environ, SHARDBASE_TEST="must-not-expand"))
            self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout), arguments)
            if os.name == "nt":
                # The caller must protect its own arguments. With benign
                # arguments, prove embedded ! paths survive even if the caller
                # had enabled delayed expansion before entering the wrapper.
                result = subprocess.run(f'{shell} /d /v:on /s /c ""{launcher}" help"',
                                        cwd=base, text=True, capture_output=True,
                                        env=dict(os.environ, SHARDBASE_TEST="must-not-expand"))
                self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout), ["help"])


class RootEntryTests(unittest.TestCase):
    def load_bootstrap(self):
        spec = importlib.util.spec_from_file_location("root_bootstrap_test", ROOT / "bootstrap.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_early_version_gate_is_parseable_before_310_and_rejects(self):
        # Syntax compatibility plus a patched version gate, also manually
        # exercised under a real older interpreter when one is available.
        ast.parse((ROOT / "bootstrap.py").read_text(), feature_version=(3, 6))
        module = self.load_bootstrap()
        output = io.StringIO()
        with patch.object(sys, "version_info", (3, 9, 20)), contextlib.redirect_stderr(output):
            self.assertEqual(module.main([]), 1)
        self.assertIn("Detected: Python 3.9.20", output.getvalue())
        self.assertIn("Python 3.10+", output.getvalue())

    def test_supported_root_delegates_with_own_location(self):
        module = self.load_bootstrap()
        with patch.object(support, "setup_main", return_value=0) as setup:
            self.assertEqual(module.main(["--help"]), 0)
        setup.assert_called_once_with(ROOT, ["--help"], bootstrap=True)

    def test_incomplete_extracted_instance_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copy2(ROOT / "bootstrap.py", root)
            result = subprocess.run([sys.executable, str(root / "bootstrap.py")], text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("expected a ShardBase instance", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(list(root.iterdir()), [root / "bootstrap.py"])

    def test_help_surface(self):
        result = subprocess.run([sys.executable, str(ROOT / "bootstrap.py"), "--help"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--runtime", result.stdout)
        self.assertIn("--bin-dir", result.stdout)
        for option in ("--force", "--root", "--repair"):
            self.assertNotIn(option, result.stdout)


if __name__ == "__main__":
    unittest.main()

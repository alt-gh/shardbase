"""Synthetic, external-instance diagnostics and no-write proofs."""

import contextlib
import hashlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _support import FIXTURES, ROOT, SCRIPTS

# isort: split
import backup_restore
import bootstrap_support as bootstrap
import doctor
import shardbase


def snapshot(root):
    return {str(path.relative_to(root)): (path.stat().st_mtime_ns,
            path.read_bytes() if path.is_file() else None) for path in root.rglob("*")}


class DoctorTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / "Example Instance"
        for name in doctor.DIRECTORIES:
            (self.root / name).mkdir(parents=True, exist_ok=True)
        for name in doctor.FILES:
            shutil.copy2(ROOT / name, self.root / name)
        (self.root / "bootstrap.py").write_text("# Synthetic marker\n")
        shutil.copytree(FIXTURES / "valid-database", self.root / "app/Blueprints/Example")
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        self.candidates = stack.enter_context(patch.object(doctor, "launcher_candidates", return_value=[]))

    def results(self):
        return doctor.diagnose(self.root)

    def check(self, code):
        return next(result for result in self.results() if result.code == code)

    def cli(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = shardbase.main(["doctor", "--root", str(self.root), "--no-color", *args])
        return status, output.getvalue()

    def database(self, name="Example"):
        destination = self.root / "app/Knowledge/Databases" / name
        shutil.copytree(FIXTURES / "valid-database", destination)
        return destination

    def launcher(self, runtime=None, root=None):
        runtime = runtime or self.base / "runtime"
        python = bootstrap.venv_python(runtime, os.name)
        python.parent.mkdir(parents=True, exist_ok=True)
        python.write_text("Synthetic interpreter")
        python.chmod(0o755)
        launcher = self.base / ("shardbase.cmd" if os.name == "nt" else "shardbase")
        launcher.write_text(bootstrap.render_launcher(python, (root or self.root) / "app/Scripts/shardbase.py", os.name))
        launcher.chmod(0o755)
        self.candidates.return_value = [launcher]
        return launcher, python

    def probe(self, version=None, prefix=None):
        return patch.object(doctor.subprocess, "run", return_value=subprocess.CompletedProcess(
            [], 0, json.dumps([version or [3, 10, 0], str(prefix or self.base / "runtime")]), ""))

    def test_fresh_instance_no_development_assets_no_writes(self):
        before = snapshot(self.root)
        with patch.object(socket, "socket", side_effect=AssertionError("No network")), patch.object(
                bootstrap, "install", side_effect=AssertionError("No installation")):
            results = self.results()
        self.assertFalse(any(result.severity == "FAIL" for result in results), results)
        self.assertIn("private ZIP-style", self.check("privacy.root_git").summary)
        self.assertEqual(self.check("runtime.launcher").severity, "INFO")
        self.assertIn("fresh instance", self.check("knowledge.state").summary)
        self.assertEqual(snapshot(self.root), before)

    def test_required_surfaces_and_root_fail_individually(self):
        for name in (*doctor.DIRECTORIES, *doctor.FILES):
            path = self.root / name
            saved = self.base / "saved"
            path.rename(saved)
            try:
                with self.subTest(name=name):
                    self.assertEqual(self.check("framework.files").severity, "FAIL")
                    self.assertEqual(self.cli()[0], 1)
            finally:
                saved.rename(path)
        for path in (self.root / "missing", self.root / "bootstrap.py"):
            self.assertEqual(doctor.diagnose(path)[0].code, "framework.root")
            self.assertEqual(doctor.diagnose(path)[0].severity, "FAIL")

    def test_bootstrap_missing_is_warning_only(self):
        (self.root / "bootstrap.py").unlink()
        self.assertEqual(self.check("framework.bootstrap").severity, "WARN")
        self.assertEqual(self.cli()[0], 0)

    def test_specification_contract_is_reused(self):
        spec = self.root / bootstrap.SPECIFICATION
        spec.write_text("Specification version: `foundation-42`\n")
        self.assertEqual(self.check("framework.spec").summary, "System Specification: foundation-42")
        for contents in (b"No declaration", b"\xff"):
            spec.write_bytes(contents)
            self.assertEqual(self.check("framework.spec").severity, "FAIL")
        with patch.object(backup_restore, "specification", side_effect=PermissionError):
            self.assertEqual(self.check("framework.spec").severity, "FAIL")

    def test_blueprint_discovery_empty_malformed_and_ambiguous(self):
        blueprint = self.root / "app/Blueprints/Example"
        self.assertEqual(self.check("framework.blueprints").severity, "OK")
        shutil.copytree(blueprint, blueprint.with_name("Duplicate"))
        self.assertEqual(self.check("framework.blueprints").severity, "FAIL")
        shutil.rmtree(blueprint.with_name("Duplicate"))
        (blueprint / "Database.md").write_text("---\ndatabase_id: [broken\n---\n")
        self.assertEqual(self.check("framework.blueprints").severity, "FAIL")
        shutil.rmtree(blueprint)
        self.assertEqual(self.check("framework.blueprints").severity, "WARN")

    def test_root_and_parent_git_markers_are_nonblocking(self):
        (self.base / ".git").mkdir()
        self.assertEqual(self.check("privacy.parent_git").severity, "WARN")
        for marker in ("file", "directory"):
            git = self.root / ".git"
            git.write_text("gitdir: example") if marker == "file" else git.mkdir()
            with patch.object(backup_restore, "git_tracked", return_value=set()):
                self.assertEqual(self.check("privacy.root_git").severity, "INFO")
                self.assertEqual(self.cli()[0], 0)
            git.unlink() if marker == "file" else git.rmdir()

    def test_git_inspection_hardened_read_only_commands(self):
        (self.root / ".git").mkdir()
        content = b"Synthetic capture\n"
        path = self.root / "app/Knowledge/Inbox/Example.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(content)
        digest = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest().encode()
        name = b"app/Knowledge/Inbox/Example.md"
        responses = [os.fsencode(self.root) + b"\n", b"100644 " + digest + b" 0\t" + name + b"\0",
                     b"HEAD\n", b"100644 blob " + digest + b"\t" + name + b"\0"]
        before = snapshot(self.root)
        def run(command, **kwargs):
            self.assertTrue({"rev-parse", "ls-files", "ls-tree"} & set(command))
            self.assertEqual(kwargs["env"]["GIT_OPTIONAL_LOCKS"], "0")
            self.assertEqual(kwargs["env"]["GIT_NO_LAZY_FETCH"], "1")
            self.assertNotIn("GIT_DIR", kwargs["env"])
            return subprocess.CompletedProcess(command, 0, responses.pop(0))
        with patch.dict(os.environ, {"GIT_DIR": "unrelated"}), patch.object(backup_restore.subprocess, "run", side_effect=run):
            self.assertEqual(self.check("privacy.tracked_knowledge").severity, "WARN")
        self.assertEqual(snapshot(self.root), before)
        for error in (OSError(), backup_restore.BackupError("Git-tracked knowledge has local changes")):
            with patch.object(backup_restore, "git_tracked", side_effect=error):
                self.assertEqual(self.check("privacy.tracked_knowledge").severity, "WARN")
                self.assertEqual(self.cli()[0], 0)
        with patch.object(backup_restore, "git_tracked", return_value=set()):
            self.assertEqual(self.check("privacy.tracked_knowledge").severity, "OK")

    def test_python_versions_and_runtime_boundaries(self):
        for version, expected in (((3, 9, 9), "FAIL"), ((3, 10, 0), "OK"), ((4, 0, 0), "OK")):
            with patch.object(sys, "version_info", version):
                self.assertEqual(self.check("runtime.python").severity, expected)
        for attribute in ("executable", "prefix"):
            with patch.object(sys, attribute, str(self.root / "runtime")):
                self.assertEqual(self.check("runtime.location").severity, "FAIL")
        self.assertEqual(self.check("runtime.location").severity, "OK")

    def test_missing_broken_dependencies_and_drift(self):
        original = doctor.importlib.import_module
        for key, (_, module) in doctor.DEPENDENCIES.items():
            for error in (ImportError("private error text"), RuntimeError("private error text")):
                def load(name):
                    if name == module:
                        raise error
                    return original(name)
                with patch.object(doctor.importlib, "import_module", side_effect=load):
                    self.assertEqual(self.check("runtime." + key).severity, "FAIL")
                    status, output = self.cli()
                    self.assertEqual(status, 1)
                    self.assertNotIn("private error text", output)
                    if key == "pyyaml":
                        self.assertEqual(self.check("knowledge.validation").severity, "INFO")
        with patch.object(backup_restore, "crypto", side_effect=OSError):
            self.assertEqual(self.check("runtime.cryptography").severity, "FAIL")
        with patch.object(doctor.importlib.metadata, "version", return_value="0.0"):
            self.assertEqual(self.check("runtime.pyyaml").severity, "WARN")
            self.assertEqual(self.cli()[0], 0)
        with patch.object(doctor.importlib.metadata, "version", side_effect=doctor.importlib.metadata.PackageNotFoundError):
            self.assertEqual(self.check("runtime.pyyaml").severity, "FAIL")

    def test_requirements_are_selected_instance_source(self):
        requirements = self.root / "app/Scripts/requirements.txt"
        requirements.write_text("PyYAML==0.0\ncryptography==0.0\n")
        self.assertEqual(self.check("runtime.pyyaml").severity, "WARN")
        requirements.write_text("unrecognized requirement\n")
        self.assertEqual(self.check("runtime.requirements").severity, "FAIL")

    def test_managed_launcher_and_probe_are_read_only(self):
        launcher, python = self.launcher()
        before = snapshot(self.base)
        with self.probe() as run:
            self.assertEqual(self.check("runtime.launcher").severity, "OK")
            command = run.call_args.args[0]
            self.assertEqual(command[:4], [str(python), "-I", "-B", "-S"])
            self.assertEqual(run.call_args.kwargs["timeout"], 10)
        self.assertEqual(snapshot(self.base), before)
        launcher.write_text(launcher.read_text() + "echo edited\n")
        with self.probe() as run:
            self.assertEqual(self.check("runtime.launcher").severity, "FAIL")
            run.assert_not_called()

    def test_wrong_target_in_instance_and_unusable_launcher(self):
        for kwargs in ({"root": self.base / "Other"}, {"runtime": self.root / "runtime"}):
            self.launcher(**kwargs)
            with self.probe() as run:
                self.assertEqual(self.check("runtime.launcher").severity, "FAIL")
                run.assert_not_called()
        _, python = self.launcher()
        with self.probe(version=[3, 9, 0]):
            self.assertEqual(self.check("runtime.launcher").severity, "FAIL")
        with self.probe(prefix=self.root):
            self.assertEqual(self.check("runtime.launcher").severity, "FAIL")
        for error in (OSError(), subprocess.TimeoutExpired("python", 10)):
            with patch.object(doctor.subprocess, "run", side_effect=error):
                self.assertEqual(self.check("runtime.launcher").severity, "FAIL")
        python.unlink()
        self.assertEqual(self.check("runtime.launcher").severity, "FAIL")

    def test_discovery_only_path_and_default_deduplicated(self):
        launcher, _ = self.launcher()
        # Call the original discovery function saved on the class below.
        with patch.object(doctor.shutil, "which", return_value=str(launcher)), patch.object(
                bootstrap, "default_paths", return_value=(self.base / "runtime", self.base)):
            self.assertEqual(DISCOVER(), [launcher])
        launcher.unlink()
        with patch.object(doctor.shutil, "which", return_value=None), patch.object(
                bootstrap, "default_paths", return_value=(self.base / "runtime", self.base)):
            self.assertEqual(DISCOVER(), [])

    def test_real_external_interpreter_probe(self):
        runtime = self.base / "real runtime"
        subprocess.run([sys.executable, "-B", "-m", "venv", "--without-pip", str(runtime)],
                       check=True, capture_output=True, cwd=self.base)
        launcher = self.base / ("shardbase.cmd" if os.name == "nt" else "shardbase")
        launcher.write_text(bootstrap.render_launcher(bootstrap.venv_python(runtime, os.name),
                           self.root / "app/Scripts/shardbase.py", os.name))
        launcher.chmod(0o755)
        self.candidates.return_value = [launcher]
        before = snapshot(self.base)
        self.assertEqual(self.check("runtime.launcher").severity, "OK")
        self.assertEqual(snapshot(self.base), before)

    def test_malformed_probe_and_nonregular_launchers(self):
        launcher, _ = self.launcher()
        for output in ("not JSON", "null", "[]", '["3.10", "prefix"]'):
            with patch.object(doctor.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, output)):
                self.assertEqual(self.check("runtime.launcher").severity, "FAIL")
        launcher.unlink()
        launcher.mkdir()
        self.assertEqual(self.check("runtime.launcher").severity, "FAIL")

    def test_symlink_knowledge_and_runtime_prefix_are_rejected(self):
        target = self.base / "unrelated"
        target.mkdir()
        knowledge = self.root / "app/Knowledge"
        try:
            knowledge.symlink_to(target, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Symlinks unavailable: {error}")
        self.assertEqual(self.check("knowledge.validation").severity, "FAIL")
        # A venv's binary can resolve outside the instance while its prefix
        # remains inside it; both must be checked independently.
        with patch.object(sys, "executable", str(Path(sys.executable).resolve())), patch.object(
                sys, "prefix", str(self.root / "runtime")):
            self.assertEqual(self.check("runtime.location").severity, "FAIL")

    def test_empty_valid_invalid_databases_and_discovery(self):
        (self.root / "app/Knowledge").mkdir()
        self.assertIn("No live databases", self.check("knowledge.databases").summary)
        database = self.database()
        self.database("Second")
        before = snapshot(self.root)
        self.assertIn("2 database(s) passed implemented structural checks", self.check("knowledge.databases").summary)
        self.assertEqual(snapshot(self.root), before)
        note = database / "Data/Game/Broken.md"
        note.write_text("# Secret body must not be echoed\n")
        before = snapshot(self.root)
        status, output = self.cli()
        self.assertEqual(status, 1)
        self.assertIn("knowledge.structural-frontmatter", output)
        self.assertIn(f"{note.relative_to(self.root)}: structural-frontmatter", output)
        self.assertNotIn("Secret body", output)
        self.assertEqual(snapshot(self.root), before)
        (database.parent / "stray.txt").write_text("Synthetic")
        self.assertEqual(self.check("knowledge.database-location").severity, "FAIL")

    def test_knowledge_file_fails_without_creating_anything(self):
        (self.root / "app/Knowledge").write_text("Synthetic")
        before = snapshot(self.root)
        self.assertEqual(self.check("knowledge.state").severity, "FAIL")
        self.assertEqual(snapshot(self.root), before)

    def test_rendering_exit_status_group_order_and_cancellation(self):
        status, output = self.cli()
        self.assertEqual(status, 0)
        positions = [output.index("\n  " + name + "\n") for name in doctor.CATEGORIES]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("\x1b", output)
        self.assertTrue(all(result.severity in {"OK", "INFO", "WARN", "FAIL"} for result in self.results()))
        with patch.dict(os.environ, {"NO_COLOR": "1"}), patch.object(sys.stdout, "isatty", return_value=True):
            self.assertFalse(shardbase.Terminal().color)
        with patch.object(doctor, "diagnose", side_effect=KeyboardInterrupt), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.cli()[0], 130)

    def test_dependency_free_subprocess_and_bound_source_no_bytecode(self):
        shutil.copytree(SCRIPTS, self.root / "app/Scripts", dirs_exist_ok=True)
        before = snapshot(self.root)
        result = subprocess.run([sys.executable, "-S", str(self.root / "app/Scripts/shardbase.py"),
                                 "doctor", "--no-color"], capture_output=True, text=True, cwd=self.base)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL  runtime.pyyaml", result.stdout)
        self.assertIn("FAIL  runtime.cryptography", result.stdout)
        self.assertIn("INFO  knowledge.validation", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertEqual(snapshot(self.root), before)

    def test_selected_root_subprocess_smoke_scenarios(self):
        environment = dict(os.environ, HOME=str(self.base), USERPROFILE=str(self.base),
                           LOCALAPPDATA=str(self.base), PATH=str(self.base))
        (self.root / bootstrap.SPECIFICATION).write_text("Specification version: `foundation-42`\n")
        command = [sys.executable, "-B", str(SCRIPTS / "shardbase.py"), "doctor",
                   "--root", str(self.root), "--no-color"]
        for scenario in ("fresh", "parent-git", "valid-database", "invalid-database"):
            if scenario == "parent-git":
                (self.base / ".git").mkdir()
            elif scenario == "valid-database":
                database = self.database()
            elif scenario == "invalid-database":
                (database / "Database.md").unlink()
            before = snapshot(self.root)
            result = subprocess.run(command, env=environment, cwd=self.base, text=True, capture_output=True)
            with self.subTest(scenario=scenario):
                self.assertEqual(result.returncode, 1 if scenario == "invalid-database" else 0, result.stdout + result.stderr)
                self.assertIn("System Specification: foundation-42", result.stdout)
                if scenario != "fresh":
                    self.assertIn("WARN  privacy.parent_git", result.stdout)
                self.assertNotIn("Traceback", result.stdout + result.stderr)
                self.assertEqual(snapshot(self.root), before)


DISCOVER = doctor.launcher_candidates


if __name__ == "__main__":
    unittest.main()

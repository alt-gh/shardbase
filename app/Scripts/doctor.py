"""Read-only instance diagnostics; structured results have no rendering dependency."""

from __future__ import annotations

import importlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import backup_restore
import bootstrap_support as bootstrap

CATEGORIES = ("Framework", "Privacy", "Runtime", "Knowledge")
DIRECTORIES = ("app", "app/Blueprints", "app/Docs", "app/Registry", "app/Scripts")
FILES = ("app/Scripts/shardbase.py", "app/Scripts/requirements.txt", bootstrap.SPECIFICATION)
DEPENDENCIES = {"pyyaml": ("PyYAML", "yaml"), "cryptography": ("cryptography", "cryptography")}


@dataclass(frozen=True)
class CheckResult:
    category: str
    code: str
    severity: Literal["OK", "INFO", "WARN", "FAIL"]
    summary: str
    detail: str | None = None


def launcher_candidates() -> list[Path]:
    """Inspect PATH and the bootstrap default only, preserving symlink leaves."""
    _, directory = bootstrap.default_paths(os.name, os.environ, Path.home())
    default = directory / ("shardbase.cmd" if os.name == "nt" else "shardbase")
    found = shutil.which("shardbase")
    candidates = ([Path(found)] if found else []) + [default]
    result, seen = [], set()
    for path in candidates:
        path = path.expanduser().absolute()
        if path.exists() or path.is_symlink():
            key = os.path.normcase(str(path.parent.resolve() / path.name))
            if key not in seen:
                result.append(path)
                seen.add(key)
    return result


def inspect_launcher(path: Path, root: Path) -> None:
    """Validate targets without executing the launcher or importing site hooks."""
    original = bootstrap.inspect_launcher(path, os.name)
    if original is None:
        raise ValueError("Launcher disappeared during inspection")
    targets = bootstrap.launcher_targets(original[-1], os.name)
    python, script = map(Path, targets)
    bootstrap.external_path(path, "Launcher", root)
    if script.resolve() != (root / "app/Scripts/shardbase.py").resolve() or not script.is_file():
        raise ValueError("Managed launcher does not target this instance's shardbase.py")
    # Check both the resolved binary and lexical venv root: venv binaries are
    # commonly symlinks to a system interpreter outside the venv itself.
    bootstrap.external_path(python, "Launcher interpreter", root)
    runtime = bootstrap.external_path(python.parent.parent, "Launcher runtime", root)
    if not python.is_file() or (os.name != "nt" and not os.access(python, os.X_OK)):
        raise ValueError("Launcher interpreter is missing or not executable")
    if os.name != "nt" and not os.access(path, os.X_OK):
        raise ValueError("Launcher is not executable")
    try:
        probe = subprocess.run(
            [str(python), "-I", "-B", "-S", "-c",
             "import json,sys; print(json.dumps([list(sys.version_info[:3]), sys.prefix]))"],
            cwd=runtime, capture_output=True, text=True, timeout=10, check=True,
        )
        version, prefix = json.loads(probe.stdout)
        if (not isinstance(version, list) or len(version) != 3
                or any(type(part) is not int for part in version) or not isinstance(prefix, str)):
            raise ValueError
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        raise ValueError("Launcher interpreter could not be safely probed") from None
    if tuple(version) < bootstrap.MINIMUM_PYTHON:
        raise ValueError("Launcher interpreter requires Python 3.10+")
    # -S reports the base prefix on Python before 3.14; inspect it for boundary
    # safety, without falsely requiring it to equal the lexical venv root.
    bootstrap.external_path(Path(prefix), "Launcher interpreter prefix", root)


def diagnose(root: Path) -> list[CheckResult]:
    """Observe the selected instance; never install, repair, or create knowledge.

    Suppress bytecode while lazily importing runtime modules even when called
    directly by another tool. Restore the caller's setting on every exit.
    """
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        return _diagnose(root)
    finally:
        sys.dont_write_bytecode = previous


def _diagnose(root: Path) -> list[CheckResult]:
    results = []

    def add(code, severity, summary, detail=None):
        results.append(CheckResult(code.split(".")[0].title(), code, severity, summary, detail))

    def attempt(code, action, severity="FAIL"):
        try:
            return action()
        except Exception as error:
            # Dependency/OS exceptions can contain source text or environment
            # values. Report the failed operation and type, never raw output.
            summaries = {
                "framework.files": "Required framework surfaces could not be inspected",
                "framework.spec": "System Specification declaration could not be safely read or parsed",
                "framework.blueprints": "Blueprint discovery failed; review malformed manifests or ambiguous identities",
                "privacy.inspection": "Git boundaries could not be inspected; review filesystem access",
                "runtime.location": "Active interpreter or runtime prefix is inside an instance/vault or cannot be resolved",
                "runtime.requirements": "Runtime requirements could not be read as supported unique dependency pins",
                "runtime.launcher": "Launcher discovery could not complete; review PATH and default launcher access",
                "knowledge.validation": "Knowledge boundary or structural validation could not be safely inspected",
            }
            add(code, severity, summaries[code], type(error).__name__)
            return None

    try:
        root = root.expanduser().resolve(strict=True)
        if not root.is_dir():
            raise ValueError
    except (OSError, ValueError, RuntimeError):
        add("framework.root", "FAIL", "Selected root must be an existing instance directory")
        for category in CATEGORIES[1:]:
            add(category.lower() + ".inspection", "INFO", "Not inspected because the selected root is unavailable")
        return results

    def framework():
        missing = [name for name in DIRECTORIES if not (root / name).is_dir()]
        missing += [name for name in FILES if not (root / name).is_file()]
        if missing:
            add("framework.files", "FAIL", "Required framework surfaces are missing or have the wrong type", ", ".join(missing))
        else:
            bootstrap.validate_instance_root(root)
            add("framework.files", "OK", "Required framework files and directories present")
        present = (root / "bootstrap.py").is_file()
        add("framework.bootstrap", "OK" if present else "WARN",
            "Root bootstrap.py present" if present else "Root bootstrap.py is missing")

    attempt("framework.files", framework)
    version = attempt("framework.spec", lambda: backup_restore.specification(root))
    if version:
        add("framework.spec", "OK", f"System Specification: {version}")

    def privacy():
        git = root / ".git"
        managed = git.exists() or git.is_symlink()
        add("privacy.root_git", "INFO" if managed else "OK",
            "Git-managed/development-style instance" if managed else "No Git repository at instance root — private ZIP-style instance")
        parents = [parent for parent in root.parents if (parent / ".git").exists() or (parent / ".git").is_symlink()]
        add("privacy.parent_git", "WARN" if parents else "OK",
            "Instance is inside another Git working-tree boundary; review whether the parent repository can include it"
            if parents else "No enclosing Git boundary found")
        if managed:
            try:
                tracked = backup_restore.git_tracked(root)
            except (OSError, ValueError, RuntimeError):
                add("privacy.tracked_knowledge", "WARN",
                    "Git tracking could not be certified; review Git availability and local changes to tracked knowledge")
            else:
                add("privacy.tracked_knowledge", "WARN" if tracked else "OK",
                    f"{len(tracked)} knowledge paths tracked by Git; review the intended sharing policy"
                    if tracked else "No Git-tracked knowledge found")

    attempt("privacy.inspection", privacy, "WARN")
    supported = sys.version_info[:2] >= bootstrap.MINIMUM_PYTHON
    add("runtime.python", "OK" if supported else "FAIL",
        f"Python {'.'.join(map(str, sys.version_info[:3]))}; Python 3.10+ required")

    def location():
        for path in (sys.executable, sys.prefix):
            bootstrap.external_path(Path(path), "Active runtime", root)
        add("runtime.location", "OK", "Active interpreter and runtime prefix are outside this instance and identifiable vaults")

    attempt("runtime.location", location)

    def requirements():
        pins = {}
        for line in (root / "app/Scripts/requirements.txt").read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s;]+)", line)
            if not match:
                raise ValueError("Expected pinned runtime requirements")
            name = re.sub(r"[-_.]+", "-", match[1]).lower()
            if name in pins or name not in DEPENDENCIES:
                raise ValueError("Unsupported or repeated runtime requirement")
            pins[name] = match[2]
        if set(pins) != set(DEPENDENCIES):
            raise ValueError("Required runtime dependency declarations are missing")
        return pins

    pins = attempt("runtime.requirements", requirements)
    available = set()
    for key, (distribution, module) in DEPENDENCIES.items():
        try:
            dependency = importlib.import_module(module)
            if key == "pyyaml":
                if dependency.safe_load("doctor: true") != {"doctor": True}:
                    raise ValueError
            else:
                backup_restore.crypto()
            installed = importlib.metadata.version(distribution)
        except Exception:
            add("runtime." + key, "FAIL", f"{distribution} is unavailable or broken; check the external runtime installation")
        else:
            available.add(key)
            drift = pins is not None and installed != pins[key]
            add("runtime." + key, "WARN" if drift else "OK",
                f"{distribution} {installed} available" + (f"; requirements.txt pins {pins[key]}" if drift else ""))

    candidates = attempt("runtime.launcher", launcher_candidates)
    if candidates == []:
        add("runtime.launcher", "INFO", "No Shardbase launcher discovered; direct/script use may be intentional")
    for candidate in candidates or []:
        try:
            inspect_launcher(candidate, root)
        except (OSError, ValueError, RuntimeError) as error:
            add("runtime.launcher", "FAIL", "Discovered launcher is unusable or does not target this instance",
                f"{candidate}: {error}")
        else:
            add("runtime.launcher", "OK", "Managed launcher targets this instance with a supported external interpreter", str(candidate))

    def blueprints():
        from database_creation import available_blueprints

        found = available_blueprints(root)
        add("framework.blueprints", "OK" if found else "WARN",
            f"{len(found)} blueprint(s) discoverable" if found else "No usable blueprints discovered")

    if "pyyaml" in available:
        attempt("framework.blueprints", blueprints)
    else:
        add("framework.blueprints", "INFO", "Blueprint discovery not run because PyYAML is unavailable")

    def knowledge():
        directory = root / "app/Knowledge"
        backup_restore.safe_path(directory)
        if directory.exists() and not directory.is_dir():
            add("knowledge.state", "FAIL", "app/Knowledge must be a directory")
            return
        add("knowledge.state", "OK", "Knowledge directory present" if directory.exists()
            else "No knowledge directory yet — valid fresh instance state")
        if "pyyaml" not in available:
            add("knowledge.validation", "INFO", "Structural validation not run because PyYAML is unavailable")
            return
        from validate_shardbase import discover_databases, validate_database

        issues = []
        databases = discover_databases(root / "app", issues)
        for database in databases:
            issues.extend(validate_database(database))
        for issue in issues:
            # Codes and paths preserve diagnostic identity without quoting
            # note titles/metadata that may occur in validator prose.
            add("knowledge." + issue.code, "FAIL", "Implemented structural check failed",
                f"{issue.path.relative_to(root)}: {issue.code}")
        if issues:
            add("knowledge.databases", "INFO", f"{len(databases)} database(s) inspected; structural issues reported above")
        else:
            add("knowledge.databases", "OK", f"{len(databases)} database(s) passed implemented structural checks"
                if databases else "No live databases found")
        add("knowledge.scope", "INFO", "Structural checks do not certify database-semantic conformance or historical specification versions")

    attempt("knowledge.validation", knowledge)
    return sorted(results, key=lambda result: CATEGORIES.index(result.category))

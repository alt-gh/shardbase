"""Stdlib-only external runtime and versioned native launcher installation."""

from __future__ import annotations

import argparse
import json
import ntpath
import os
import re
import shlex
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath

MINIMUM_PYTHON = (3, 10)
SPECIFICATION = "app/Docs/Shard System Specification.md"
MARKER = "SHARDBASE-MANAGED-LAUNCHER: 1"
POSIX_HEADER = "#!/bin/sh\n# " + MARKER + "\n"
# Preserve the historical signature so existing launchers remain recognizable.
LEGACY_HEADER = "#!/bin/sh\n# ShardBase launcher; source and knowledge remain in the selected checkout.\n"
WINDOWS_HEADER = "@echo off\nrem " + MARKER + "\nsetlocal DisableDelayedExpansion\n"


class SetupError(ValueError):
    """An expected installation failure with an actionable user message."""


def validate_instance_root(root: Path) -> Path:
    root = root.resolve()
    for marker in ("app/Scripts/shardbase.py", "app/Scripts/requirements.txt", SPECIFICATION):
        if not (root / marker).is_file():
            raise SetupError(f"Expected a Shardbase instance containing {marker}: {root}")
    return root


def default_paths(platform: str, environment, home: Path) -> tuple[Path, Path]:
    if platform == "nt":
        local = environment.get("LOCALAPPDATA")
        base = (Path(local) if local else home / "AppData/Local") / "Shardbase"
        return base / "venv", base / "bin"
    return home / ".local/share/shardbase/venv", home / ".local/bin"


def external_path(path: Path, label: str, instance_root: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == instance_root or resolved.is_relative_to(instance_root):
        raise SetupError(f"{label} must be outside the Shardbase project/vault.")
    for ancestor in (resolved, *resolved.parents):
        if (ancestor / SPECIFICATION).is_file() or (ancestor / ".obsidian").is_dir():
            raise SetupError(f"{label} must be outside every Shardbase instance and Obsidian vault.")
    return resolved


def venv_python(runtime: Path, platform: str) -> Path:
    return runtime / ("Scripts/python.exe" if platform == "nt" else "bin/python")


def run_step(command, label: str, **kwargs):
    try:
        return subprocess.run(command, check=True, **kwargs)
    except (OSError, subprocess.CalledProcessError) as error:
        raise SetupError(f"{label} failed: {error}") from error


def prepare_runtime(runtime: Path, platform: str, environment, temp_dir: Path) -> Path:
    python = venv_python(runtime, platform)
    if not runtime.exists():
        run_step([sys.executable, "-B", "-m", "venv", str(runtime)],
                 "Virtual environment creation (check Python's venv/ensurepip support; "
                 "any partial runtime is preserved, choose another --runtime to retry)",
                 env=environment, cwd=temp_dir)
    if not (runtime / "pyvenv.cfg").is_file() or not python.is_file():
        raise SetupError("The runtime directory already exists but is not a usable virtual environment; "
                         "it has been preserved. Choose another --runtime.")
    result = run_step([str(python), "-B", "-c",
                       "import json,sys; print(json.dumps([list(sys.version_info[:3]), sys.prefix]))"],
                      "Runtime interpreter check (choose another --runtime if unusable)",
                      env=environment, cwd=temp_dir, capture_output=True, text=True)
    try:
        version, prefix = json.loads(result.stdout)
        valid = (isinstance(version, list) and len(version) == 3
                 and all(type(part) is int for part in version) and isinstance(prefix, str))
    except (ValueError, TypeError):
        valid = False
    if not valid:
        raise SetupError("Runtime interpreter returned invalid version information; choose another --runtime.")
    if tuple(version) < MINIMUM_PYTHON:
        raise SetupError(f"Runtime uses Python {'.'.join(map(str, version))}; Python 3.10+ is required. "
                         "Runtime preserved; choose another --runtime.")
    if Path(prefix).resolve() != runtime:
        raise SetupError("Runtime interpreter does not belong to this virtual environment; choose another --runtime.")
    return python


def render_launcher(python, script, platform: str) -> str:
    python, script = str(python), str(script)
    if any(char in python + script for char in "\r\n\0"):
        raise SetupError("Launcher paths must not contain newlines or NUL characters.")
    if platform == "nt":
        if '"' in python + script:
            raise SetupError('Windows launcher paths must not contain double quotes.')
        # Percent expansion happens inside quotes too. Delayed expansion is off
        # so literal ! survives; quoted paths protect &, ^, (, and ). No CALL.
        python, script = python.replace("%", "%%"), script.replace("%", "%%")
        return WINDOWS_HEADER + f'"{python}" -B "{script}" %*\nexit /b %errorlevel%\n'
    return POSIX_HEADER + f'exec {shlex.quote(python)} -B {shlex.quote(script)} "$@"\n'


def launcher_targets(contents: str, platform: str) -> tuple[str, str] | None:
    """Recognize the complete canonical format, never just a marker/filename.

    The exact pre-marker POSIX format is supported for existing installations.
    Unknown versions or edited commands are deliberately not recognized.
    """
    try:
        if platform == "nt":
            match = re.fullmatch(re.escape(WINDOWS_HEADER) + r'"([^"\n]+)" -B "([^"\n]+)" %\*\nexit /b %errorlevel%\n', contents)
            if not match:
                return None
            python, script = (part.replace("%%", "%") for part in match.groups())
            path_type, interpreter_tail = PureWindowsPath, ("Scripts", "python.exe")
            expected = render_launcher(python, script, platform)
        else:
            header = LEGACY_HEADER if contents.startswith(LEGACY_HEADER) else POSIX_HEADER
            if not contents.startswith(header):
                return None
            tokens = shlex.split(contents[len(header):])
            if len(tokens) != 5 or tokens[0] != "exec" or tokens[2] != "-B" or tokens[4] != "$@":
                return None
            python, script = tokens[1], tokens[3]
            path_type, interpreter_tail = PurePosixPath, ("bin", "python")
            expected = render_launcher(python, script, platform).replace(POSIX_HEADER, header, 1)
        recognized = (contents == expected and path_type(python).is_absolute() and path_type(script).is_absolute()
                and path_type(python).parts[-2:] == interpreter_tail
                and path_type(script).parts[-3:] == ("app", "Scripts", "shardbase.py"))
        return (python, script) if recognized else None
    except ValueError:
        return None


def managed_launcher(contents: str, platform: str) -> bool:
    """Recognize only the complete supported managed launcher formats."""
    return launcher_targets(contents, platform) is not None


def inspect_launcher(launcher: Path, platform: str):
    try:
        info = launcher.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode):
        raise SetupError(f"Unexpected launcher path (symlink or non-regular file); preserved: {launcher}")
    try:
        contents = launcher.read_text(encoding="utf-8")
    except UnicodeError as error:
        raise SetupError(f"Unrecognized launcher preserved: {launcher}") from error
    if not managed_launcher(contents, platform):
        raise SetupError(f"An existing shardbase launcher differs from supported managed formats; "
                         f"preserved: {launcher}. Choose another --bin-dir or review it first.")
    return (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size, contents)


def publish_launcher(launcher: Path, contents: str, platform: str, original) -> None:
    launcher.parent.mkdir(parents=True, exist_ok=True)
    if inspect_launcher(launcher, platform) != original:
        raise SetupError("Launcher changed during setup; preserved. Review it and rerun bootstrap.")
    if original and original[-1] == contents:
        return
    # Stage on the same external filesystem, then recheck immediately before
    # publication. No-clobber hard linking protects absent destinations; replace
    # of an existing managed file assumes no concurrent edits after this check.
    descriptor, name = tempfile.mkstemp(prefix=".shardbase-", dir=launcher.parent)
    staging = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(contents)
        if platform != "nt":
            staging.chmod(0o755)
        if inspect_launcher(launcher, platform) != original:
            raise SetupError("Launcher changed during setup; preserved. Review it and rerun bootstrap.")
        if original is None:
            os.link(staging, launcher)
        else:
            os.replace(staging, launcher)
    finally:
        staging.unlink(missing_ok=True)


def install(instance_root: Path, runtime: Path, bin_dir: Path, *, platform=None, environment=None) -> Path:
    platform = platform or os.name
    environment = dict(os.environ if environment is None else environment)
    root = validate_instance_root(instance_root)
    runtime = external_path(runtime, "Runtime directory", root)
    bin_dir = external_path(bin_dir, "Launcher directory", root)
    temp_dir = external_path(Path(tempfile.gettempdir()), "Temporary directory", root)
    environment.update(PYTHONDONTWRITEBYTECODE="1", PIP_NO_CACHE_DIR="1", PIP_NO_COMPILE="1",
                       TMPDIR=str(temp_dir), TEMP=str(temp_dir), TMP=str(temp_dir))
    launcher = bin_dir / ("shardbase.cmd" if platform == "nt" else "shardbase")
    script = root / "app/Scripts/shardbase.py"
    contents = render_launcher(venv_python(runtime, platform), script, platform)
    original = inspect_launcher(launcher, platform)
    python = prepare_runtime(runtime, platform, environment, temp_dir)
    print("Installing pinned Shardbase runtime dependencies.\n"
          "This step may access configured Python package indexes/network resources.", flush=True)
    run_step([str(python), "-B", "-m", "pip", "--isolated", "install", "--no-cache-dir",
              "--no-compile", "--disable-pip-version-check", "-r", str(root / "app/Scripts/requirements.txt")],
             "Dependency installation (check package-index access and rerun bootstrap)", env=environment, cwd=runtime)
    publish_launcher(launcher, contents, platform, original)
    run_step([str(python), "-B", str(script), "commands"], "CLI smoke check", env=environment, cwd=temp_dir)
    print("CLI check passed.")
    return launcher


def launcher_on_path(bin_dir: Path, platform: str, environment) -> bool:
    entries = environment.get("PATH", "").split(";" if platform == "nt" else os.pathsep)
    def normalize(value):
        if platform == "nt":
            return ntpath.normcase(ntpath.abspath(value))
        return str(Path(value).resolve())
    return any(normalize(entry.strip('"')) == normalize(str(bin_dir)) for entry in entries if entry)


def report_completion(
    root: Path, runtime: Path, launcher: Path, platform: str, environment, *, manual_next_step: bool = True
) -> None:
    print(f"\nShardbase tooling is ready.\nRuntime: {runtime}\nLauncher: {launcher}")
    if launcher_on_path(launcher.parent, platform, environment):
        print(f"Launcher directory is on PATH: {launcher.parent}")
    else:
        print(f"Launcher directory is not on PATH: {launcher.parent}\nFor this terminal session:")
        if platform == "nt":
            escaped = str(launcher.parent).replace("'", "''")
            print(f"  PowerShell: $env:Path = '{escaped};' + $env:Path")
        else:
            print(f'  export PATH={shlex.quote(str(launcher.parent))}:"$PATH"')
        print("Persistent PATH configuration is your choice; no shell/profile settings were changed.")
    print(f"Selected instance: {root}")
    if manual_next_step:
        print("Next:\n  shardbase init")


def onboarding_appropriate(root: Path) -> bool:
    """Return true only for an observably fresh private knowledge boundary."""
    knowledge = root / "app/Knowledge"
    if not knowledge.exists():
        return not knowledge.is_symlink()
    if knowledge.is_symlink() or not knowledge.is_dir():
        return False
    try:
        return next(knowledge.iterdir(), None) is None
    except OSError:
        return False


def interactive_terminal() -> bool:
    return all(stream.isatty() for stream in (sys.stdin, sys.stdout, sys.stderr))


def handoff_to_initialization(root: Path, python: Path, environment) -> int:
    """Run guided setup directly with the prepared runtime, never through PATH."""
    script = root / "app/Scripts/shardbase.py"
    print("\nStarting guided setup with the prepared external runtime.")
    try:
        result = subprocess.run(
            [str(python), "-B", str(script), "init", "--root", str(root)],
            env=dict(environment, PYTHONDONTWRITEBYTECODE="1"),
            check=False,
        )
    except OSError as error:
        print(
            f"Guided setup could not start: {error}\n"
            "Tooling remains installed. Run manually:\n  shardbase init",
            file=sys.stderr,
        )
        return 1
    if result.returncode == 130:
        print("Guided setup was cancelled. The prepared runtime and launcher were preserved.", file=sys.stderr)
    elif result.returncode:
        print(
            "Guided setup did not complete. The prepared runtime and launcher were preserved.\n"
            "Retry with:\n  shardbase init",
            file=sys.stderr,
        )
    return result.returncode


def setup_main(instance_root: Path, argv=None, *, bootstrap=False) -> int:
    platform = os.name
    runtime, bin_dir = default_paths(platform, os.environ, Path.home())
    parser = argparse.ArgumentParser(description="Prepare external Shardbase tooling for this instance.")
    parser.add_argument("--runtime", type=Path, default=runtime, help=f"External virtual environment (default: {runtime})")
    parser.add_argument("--bin-dir", type=Path, default=bin_dir, help=f"External launcher directory (default: {bin_dir})")
    args = parser.parse_args(argv)
    try:
        root = validate_instance_root(instance_root)
        if bootstrap:
            print("Shardbase bootstrap\n")
        if (root / ".git").is_file() or (root / ".git").is_dir():
            print("Git-managed/development instance detected.")
        else:
            print("Private instance mode\nNo Git repository detected at the instance root.\n"
                  "This instance is locally isolated from the public Shardbase repository.")
        launcher = install(root, args.runtime, args.bin_dir)
        resolved_runtime = args.runtime.expanduser().resolve()
        private = not ((root / ".git").exists() or (root / ".git").is_symlink())
        automatic_init = bootstrap and private and interactive_terminal() and onboarding_appropriate(root)
        report_completion(
            root, resolved_runtime, launcher, platform, os.environ, manual_next_step=not automatic_init
        )
        if automatic_init:
            return handoff_to_initialization(root, venv_python(resolved_runtime, platform), os.environ)
    except (SetupError, OSError) as error:
        print(f"Setup failed: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nSetup cancelled; any partial external runtime is preserved.", file=sys.stderr)
        return 130
    return 0

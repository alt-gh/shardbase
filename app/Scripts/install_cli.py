#!/usr/bin/env python3
"""Install a POSIX shardbase launcher and Python runtime outside the vault."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

PROJECT = Path(__file__).resolve().parents[2]


def external_path(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == PROJECT or resolved.is_relative_to(PROJECT):
        raise ValueError(f"{label} must be outside the ShardBase project/vault.")
    # Also reject another identifiable ShardBase instance or Obsidian vault.
    for ancestor in (resolved, *resolved.parents):
        if (ancestor / "app/Docs/Shard System Specification.md").is_file() or (ancestor / ".obsidian").is_dir():
            raise ValueError(f"{label} must be outside every ShardBase instance and Obsidian vault.")
    return resolved


def install(runtime: Path, bin_dir: Path) -> Path:
    if os.name != "posix":
        raise ValueError("This launcher installer supports macOS/Linux. Use the documented direct Python commands on other platforms.")
    runtime = external_path(runtime, "Runtime directory")
    bin_dir = external_path(bin_dir, "Launcher directory")
    external_path(Path(tempfile.gettempdir()), "Temporary directory")
    python = runtime / "bin/python"
    launcher = bin_dir / "shardbase"
    script = PROJECT / "app/Scripts/shardbase.py"
    contents = (
        "#!/bin/sh\n"
        "# ShardBase launcher; source and knowledge remain in the selected checkout.\n"
        f"exec {shlex.quote(str(python))} -B {shlex.quote(str(script))} \"$@\"\n"
    )
    def check_launcher() -> None:
        if launcher.is_symlink() or (launcher.exists() and (
            not launcher.is_file() or launcher.read_text(encoding="utf-8") != contents
        )):
            raise ValueError("An existing shardbase launcher differs; choose another --bin-dir or review the existing launcher first.")

    check_launcher()
    if runtime.exists() and not ((runtime / "pyvenv.cfg").is_file() and python.is_file()):
        raise ValueError("The runtime directory already exists but is not a usable virtual environment; choose another --runtime.")
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if not runtime.exists():
        subprocess.run([sys.executable, "-B", "-m", "venv", str(runtime)], check=True,
                       env=environment, cwd=tempfile.gettempdir())
    subprocess.run([
        str(python), "-B", "-m", "pip", "--isolated", "install", "--no-cache-dir",
        "--no-compile", "--disable-pip-version-check", "-r", str(PROJECT / "app/Scripts/requirements.txt"),
    ], check=True, env=environment, cwd=runtime)
    bin_dir.mkdir(parents=True, exist_ok=True)
    check_launcher()
    if not launcher.exists():
        with launcher.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(contents)
    launcher.chmod(0o755)
    return launcher


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, default=Path.home() / ".local/share/shardbase/venv",
                        help="External virtual environment (default: ~/.local/share/shardbase/venv)")
    parser.add_argument("--bin-dir", type=Path, default=Path.home() / ".local/bin",
                        help="External launcher directory (default: ~/.local/bin)")
    args = parser.parse_args(argv)
    try:
        launcher = install(args.runtime, args.bin_dir)
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Setup failed: {error}", file=sys.stderr)
        return 1
    print(f"\nInstalled: {launcher}")
    print("Add this directory to PATH in your shell configuration if needed:")
    print(f"  export PATH={shlex.quote(str(launcher.parent))}:\"$PATH\"")
    print("Then run: shardbase commands")
    print("Default instance: the checkout used for installation. Use --root to select another instance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

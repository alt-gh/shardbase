"""Networked bootstrap proof for CI/manual use; operates only on disposable copies."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def snapshot(root):
    return {path.relative_to(root): path.read_bytes() if path.is_file() else None
            for path in root.rglob("*")}


def run(command, cwd):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    print(result.stdout, end="")
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command}\n{result.stderr}")
    return result


def main():
    with tempfile.TemporaryDirectory(prefix="shardbase-bootstrap-") as temporary:
        base = Path(temporary).resolve()
        runtime = base / "external runtime"
        bin_dir = base / "external bin"
        launcher = bin_dir / ("shardbase.cmd" if os.name == "nt" else "shardbase")
        copies = []
        for name in ("ZIP A", "ZIP B"):
            root = base / name
            (root / "app/Docs").mkdir(parents=True)
            shutil.copy2(ROOT / "bootstrap.py", root)
            shutil.copytree(ROOT / "app/Scripts", root / "app/Scripts",
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            shutil.copy2(ROOT / "app/Docs/Shard System Specification.md", root / "app/Docs")
            copies.append(root)
        before = [snapshot(root) for root in copies]
        for root in (copies[0], copies[0], copies[1]):
            command = [sys.executable, str(root / "bootstrap.py"),
                       "--runtime", str(runtime), "--bin-dir", str(bin_dir)]
            result = run(command, base)
            assert "Private instance mode" in result.stdout
            assert "tooling is ready" in result.stdout
            contents = launcher.read_text()
            assert str(root) in contents
            result = run([str(launcher), "commands"], base)
            assert "shardbase create new database" in result.stdout
        assert before == [snapshot(root) for root in copies], "Bootstrap changed a ZIP instance"
        launcher.write_bytes(b"Unrelated command\n")
        collision = subprocess.run(command, cwd=base, text=True, capture_output=True)
        assert collision.returncode != 0
        assert launcher.read_bytes() == b"Unrelated command\n"
        assert "Traceback" not in collision.stderr
        print("Bootstrap smoke passed: fresh ZIP, rerun, launcher execution, retarget, collision, instance preservation.")


if __name__ == "__main__":
    main()

"""Materialize a selected blueprint into a new user-owned database only."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from note_creation import CreationError, checked_path, read_document, refuse_collision
from validate_shardbase import nonempty_string, portable_component, validate_database


@dataclass(frozen=True)
class Blueprint:
    path: Path
    database_id: str
    database_name: str


def instance_root(root: Path) -> Path:
    root = root.resolve(strict=True)
    if not checked_path(root, root / "app").is_dir():
        raise CreationError("--root must select an instance directory containing app/.")
    return root


def available_blueprints(root: Path) -> list[Blueprint]:
    root = instance_root(root)
    directory = checked_path(root, root / "app/Blueprints")
    if not directory.exists():
        return []
    result = []
    identities = set()
    for path in sorted(directory.iterdir()):
        checked_path(root, path)
        if not path.is_dir():
            continue
        manifest = checked_path(root, path / "Database.md")
        if not manifest.is_file():
            continue
        metadata, _ = read_document(root, manifest)
        identity, name = metadata.get("database_id"), metadata.get("database_name")
        if not nonempty_string(identity) or not nonempty_string(name):
            raise CreationError(f"{manifest}: database_id and database_name must be non-empty strings.")
        if identity in identities:
            raise CreationError(f"Multiple blueprints declare database_id: {identity}; resolve the ambiguity first.")
        identities.add(identity)
        result.append(Blueprint(path, identity, name))
    return result


def inspect_package(root: Path, source: Path) -> None:
    """Reject links, special files, and generated state before copying anything."""
    generated = {".git", ".venv", "venv", "env", "ENV", "__pycache__", "node_modules",
                 ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "dist", "pyvenv.cfg"}
    for path in sorted(source.iterdir()):
        checked_path(root, path)
        if path.name in generated or path.suffix in {".pyc", ".pyo"} or path.name.endswith(".egg-info"):
            raise CreationError(f"Remove generated runtime/build state from the blueprint before copying: {path}")
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            inspect_package(root, path)
        elif not stat.S_ISREG(mode):
            raise CreationError(f"Blueprint resources must be ordinary files or directories: {path}")


def check_destination(root: Path, blueprint: Blueprint, directory: Path) -> None:
    for path in (root / "app/Knowledge", root / "app/Knowledge/Inbox", directory):
        checked_path(root, path)
        if path.exists() and not path.is_dir():
            raise CreationError(f"Expected a directory: {path}")
    refuse_collision(directory, blueprint.path.name)
    if not directory.exists():
        return
    for path in sorted(directory.iterdir()):
        checked_path(root, path)
        if path.name == ".gitkeep":
            continue
        manifest = checked_path(root, path / "Database.md")
        if not path.is_dir() or not manifest.is_file():
            raise CreationError(f"Review the incomplete existing database before creating another: {path}")
        metadata, _ = read_document(root, manifest)
        if not nonempty_string(metadata.get("database_id")):
            raise CreationError(f"Cannot establish existing database identity: {manifest}")
        if metadata["database_id"] == blueprint.database_id:
            raise CreationError(f"A live database already declares database_id: {blueprint.database_id}; existing files are never merged or replaced.")


def rebase_framework_links(text: str, root: Path, original: Path, destination: Path) -> str:
    """Relocate inline relative Markdown links to framework docs/resources only.

    Local database links, URLs, wikilinks, and fenced/inline code stay unchanged.
    Blueprint authors should use URL-encoded inline links for framework references.
    """
    framework = [root / "app" / name for name in ("Docs", "Scripts", "Registry")]

    def replace(match: re.Match) -> str:
        url = urlsplit(match[2])
        if url.scheme or url.netloc or not url.path.startswith("../"):
            return match[0]
        target = (original.parent / unquote(url.path)).resolve()
        if not any(target.is_relative_to(base) for base in framework):
            return match[0]
        relative = Path(os.path.relpath(target, destination.parent)).as_posix()
        address = urlunsplit(("", "", quote(relative, safe="/"), url.query, url.fragment))
        return match[1] + address + ")"

    result = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence:
            result.append(line)
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            continue
        if marker:
            fence = marker[1]
            result.append(line)
            continue
        # Match complete links first, allowing backticks in their labels; code
        # spans outside links are consumed unchanged by the other alternative.
        pattern = r"`+[^`\n]*`+|(\[[^\]\n]*\]\()([^\s()]+)\)"
        result.append(re.sub(pattern, lambda match: replace(match) if match[1] else match[0], line))
    return "".join(result)


def copy_new_file(source: str, destination: str) -> str:
    with open(source, "rb") as reader, open(destination, "xb") as writer:
        shutil.copyfileobj(reader, writer)
    return destination


def create_database(root: Path, blueprint_id: str) -> Path:
    root = instance_root(root)
    matches = [item for item in available_blueprints(root) if item.database_id == blueprint_id]
    if len(matches) != 1:
        raise CreationError(f"No blueprint declares database_id: {blueprint_id}.")
    blueprint = matches[0]
    if portable_component(blueprint.path.name) != blueprint.path.name:
        raise CreationError("The blueprint folder needs a portable name before it can become a database folder.")
    metadata, _ = read_document(root, blueprint.path / "Database.md")
    if metadata.get("database_status") not in ("active", "draft"):
        raise CreationError("Only active or draft blueprints can bootstrap a new database.")
    directory = root / "app/Knowledge/Databases"
    destination = directory / blueprint.path.name
    check_destination(root, blueprint, directory)
    inspect_package(root, blueprint.path)
    temporary = Path(tempfile.gettempdir()).resolve()
    project = Path(__file__).resolve().parents[2]
    if temporary.is_relative_to(root) or temporary.is_relative_to(project) or any(
        (parent / ".obsidian").is_dir() or (parent / "app/Docs/Shard System Specification.md").is_file()
        for parent in (temporary, *temporary.parents)
    ):
        raise CreationError("The temporary directory must be outside the project and knowledge vaults.")
    with tempfile.TemporaryDirectory(prefix="shardbase-blueprint-", dir=temporary) as scratch:
        staged = Path(scratch) / "app/Knowledge/Databases" / blueprint.path.name
        shutil.copytree(blueprint.path, staged, symlinks=True)
        # Recheck the copied tree as well, so links cannot enter via a changed source.
        inspect_package(Path(scratch).resolve(), staged)
        for path in sorted(staged.rglob("*.md")):
            relative = path.relative_to(staged)
            text = path.read_text(encoding="utf-8")
            rebased = rebase_framework_links(text, root, blueprint.path / relative, destination / relative)
            if rebased != text:
                path.write_text(rebased, encoding="utf-8", newline="\n")
        issues = validate_database(staged)
        if issues:
            details = "\n".join(issue.render(staged) for issue in issues)
            raise CreationError(f"Blueprint failed structural validation; no live database was written:\n{details}")
        check_destination(root, blueprint, directory)
        directory.mkdir(parents=True, exist_ok=True)
        (root / "app/Knowledge/Inbox").mkdir(exist_ok=True)
        try:
            # copytree reserves the destination exclusively; individual files also
            # use exclusive writes. Never merge, overwrite, or delete live state.
            shutil.copytree(staged, destination, copy_function=copy_new_file)
        except OSError as error:
            raise CreationError(
                f"Database copy did not complete at {destination}. Existing files were not replaced. "
                "Inspect any partial new folder before retrying; no automatic cleanup was performed."
            ) from error
    return destination
